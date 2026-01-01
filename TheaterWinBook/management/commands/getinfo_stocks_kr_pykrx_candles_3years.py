import os
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from pykrx import stock as krx
from TheaterWinBook.models_stock_korea import StocksKrList, StocksKrCandle


class Command(BaseCommand):
    help = 'Pykrx를 사용하여 모든 국내 종목의 과거 3년치 캔들 데이터를 고속 수집합니다.'

    def handle(self, *args, **options):
        start_time = timezone.now()

        # 1. 수집 기간 설정 (최근 3년)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=3 * 365)).strftime('%Y%m%d')

        active_stocks = StocksKrList.objects.filter(is_active=True).order_by('stock_code')
        total_active = active_stocks.count()

        self.stdout.write(self.style.SUCCESS(f"🚀 [벌크 작업] 3년치 데이터 수집 시작: {start_date} ~ {end_date}"))

        processed_count = 0
        total_saved_rows = 0
        failed_stocks = []

        # Decimal 변환 헬퍼 함수
        def to_decimal(val):
            if val is None or pd.isna(val):
                return Decimal('0.0')
            return Decimal(str(val))

        for stock_obj in active_stocks:
            ticker = stock_obj.stock_code
            try:
                # 데이터 호출
                df = krx.get_market_ohlcv_by_date(fromdate=start_date, todate=end_date, ticker=ticker)

                if df.empty:
                    continue

                # 컬럼 표준화 및 NaN 처리
                df = df.rename(columns={
                    '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close',
                    '거래량': 'Volume', '거래대금': 'Value', '등락률': 'Change'
                })
                df = df.replace({np.nan: 0.0})
                df = df.reset_index()

                # 메모리에 저장할 객체 리스트
                candle_instances = []

                for _, row in df.iterrows():
                    c_date = row.get('날짜', row.get('Date'))
                    vol = int(row.get('Volume', 0))

                    if vol == 0 or pd.isna(c_date):
                        continue

                    # 인스턴스 생성 (DB 저장 전)
                    candle_instances.append(StocksKrCandle(
                        stock_code=stock_obj,
                        date=c_date.date(),
                        open_price=to_decimal(row.get('Open')),
                        high_price=to_decimal(row.get('High')),
                        low_price=to_decimal(row.get('Low')),
                        close_price=to_decimal(row.get('Close')),
                        volume=vol,
                        trade_value=int(row.get('Value', 0)),
                        change_rate=to_decimal(row.get('Change')) / 100,
                    ))

                # 💡 [CTO's Choice] Bulk Create 실행
                # ignore_conflicts=True: 중복된 날짜가 있어도 에러 없이 건너뜁니다.
                if candle_instances:
                    with transaction.atomic():
                        StocksKrCandle.objects.bulk_create(
                            candle_instances,
                            batch_size=500,  # 500개씩 묶어서 저장 (성능 최적화)
                            ignore_conflicts=True
                        )
                    total_saved_rows += len(candle_instances)

                processed_count += 1
                if processed_count % 50 == 0:
                    self.stdout.write(
                        f"[{processed_count}/{total_active}] {ticker} 완료.. (누적 적재: {total_saved_rows:,}건)")

                # API 차단 방지를 위한 미세 지연
                time.sleep(0.05)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Fail {ticker}: {e}"))
                failed_stocks.append(ticker)

        # 결과 요약
        duration = (timezone.now() - start_time).total_seconds()
        self.stdout.write(self.style.SUCCESS(f"✅ 벌크 수집 완료: 총 {total_saved_rows:,}건 적재 / 소요시간: {duration / 60:.1f}분"))