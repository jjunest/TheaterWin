import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

import FinanceDataReader as fdr
from TheaterWinBook.models_stock_usa import StocksUsList, StocksUsCandle
from TheaterWinBook.utils_telegram import send_notification_telegram


class Command(BaseCommand):
    help = '미국 주식 3년치 과거 캔들 데이터 전수 수집'

    def convert_ticker(self, symbol):
        """야후 파이낸스 규격으로 티커 변환"""
        return symbol.replace(' PR ', '-P').replace('.', '-').replace(' ', '-')

    def handle(self, *args, **options):
        start_time = timezone.now()

        # [CTO 변경 포인트 1] 수집 기간을 3년(365 * 3)으로 설정
        # 2026년 기준 2023년 데이터부터 수집합니다.
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365 * 3)).strftime('%Y-%m-%d')

        active_stocks = StocksUsList.objects.filter(is_active=True).order_by('symbol')
        total_active = active_stocks.count()

        self.stdout.write(self.style.SUCCESS(f"🚀 미국 주식 3년치 전수 수집 시작 ({total_active} 종목)"))
        self.stdout.write(f"📅 수집 기간: {start_date} ~ {end_date}")

        processed_count = 0
        success_save_count = 0
        failed_stocks = []

        for stock_obj in active_stocks:
            search_symbol = self.convert_ticker(stock_obj.symbol)

            try:
                # FDR 데이터 호출 (3년치)
                df = fdr.DataReader(search_symbol, start_date, end_date)

                if df is None or df.empty:
                    continue

                # 데이터 정제 및 인덱스 처리
                df.index.name = 'date_col'
                df = df.reset_index()
                df.columns = [c.lower().replace(' ', '') for c in df.columns]

                # [CTO 변경 포인트 2] 종목별 대량 데이터 처리를 위한 트랜잭션 최적화
                with transaction.atomic():
                    for _, row in df.iterrows():
                        c_date = row.get('date_col')
                        if c_date is None:
                            c_date = row.iloc[0]

                        if pd.isna(c_date):
                            continue

                        # 날짜 변환
                        if isinstance(c_date, (pd.Timestamp, datetime)):
                            target_date = c_date.date()
                        else:
                            target_date = pd.to_datetime(c_date).date()

                        # 거래량 0 스킵
                        vol = int(row.get('volume', 0))
                        if vol == 0: continue

                        def to_dec(val):
                            if val is None or pd.isna(val) or val == '': return Decimal('0.0000')
                            return Decimal(str(val))

                        # 데이터 저장 (3년치이므로 이미 있는 데이터는 업데이트, 없으면 생성)
                        _, created = StocksUsCandle.objects.update_or_create(
                            symbol=stock_obj,
                            date=target_date,
                            defaults={
                                'open_price': to_dec(row.get('open')),
                                'high_price': to_dec(row.get('high')),
                                'low_price': to_dec(row.get('low')),
                                'close_price': to_dec(row.get('close')),
                                'adj_close': to_dec(row.get('adjclose', row.get('close'))),
                                'volume': vol,
                            }
                        )
                        success_save_count += 1

                processed_count += 1
                # 진행률 출력 주기 조절 (데이터가 많으므로 50종목마다 출력)
                if processed_count % 50 == 0:
                    elapsed = (timezone.now() - start_time).total_seconds()
                    self.stdout.write(
                        f"[{processed_count}/{total_active}] 진행 중... (누적 저장: {success_save_count}건, 소요시간: {elapsed / 60:.1f}분)")

                # 야후 파이낸스 차단 방지를 위한 미세 대기 시간
                time.sleep(0.1)

            except Exception as e:
                # 에러 로그 상세화
                self.stdout.write(self.style.ERROR(f"❌ {stock_obj.symbol} 처리 실패: {str(e)}"))
                failed_stocks.append(f"{stock_obj.symbol}")
                continue

        # 최종 보고
        duration = (timezone.now() - start_time).total_seconds()
        summary = (
            f"**미국 주식 3년치 데이터 수집 완료**\n"
            f"- 대상 종목: {total_active}개\n"
            f"- 성공 종목: {processed_count}개\n"
            f"- 실패 종목: {len(failed_stocks)}개\n"
            f"- 총 저장 건수: {success_save_count}건\n"
            f"- 총 소요시간: {duration / 60:.1f}분"
        )
        send_notification_telegram(summary, level="SUCCESS", category="미국주식")