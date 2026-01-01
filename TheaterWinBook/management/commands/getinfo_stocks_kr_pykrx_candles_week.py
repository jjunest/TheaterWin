import os
import time
import traceback
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db import transaction

# FDR 대신 pykrx 임포트
from pykrx import stock as krx
import pandas as pd

from TheaterWinBook.models_stock_korea import StocksKrList, StocksKrCandle


def send_notification_telegram(message, level="INFO"):
    """텔레그램 알림 헬퍼 함수"""
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        API_URL = f"https://api.telegram.org/bot{token}/sendMessage"
        tag = {"FATAL": "🚨 [Pykrx-치명적] 🚨\n", "ERROR": "❌ [Pykrx-오류] ❌\n", "SUCCESS": "✅ [Pykrx-완료] ✅\n"}.get(level,
                                                                                                             "ℹ️")
        full_message = tag + message
        requests.post(API_URL, data={'chat_id': chat_id, 'text': full_message[:3900], 'parse_mode': 'Markdown'},
                      timeout=5)
    except Exception:
        pass


class Command(BaseCommand):
    help = 'Pykrx를 사용하여 ETF 포함 모든 국내 주식의 캔들 데이터를 수집합니다.'

    def handle(self, *args, **options):
        start_time = timezone.now()
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

        # 1. 수집 기간 설정
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')

        active_stocks = StocksKrList.objects.filter(is_active=True)
        total_active = active_stocks.count()

        self.stdout.write(self.style.SUCCESS(f"🚀 Pykrx 수집 시작: {start_date} ~ {end_date}"))

        processed_count = 0
        failed_stocks = []

        for stock_obj in active_stocks:
            ticker = stock_obj.stock_code

            try:
                df = krx.get_market_ohlcv_by_date(fromdate=start_date, todate=end_date, ticker=ticker)
                print("this is df:",df)
                if df.empty:
                    continue

                # [CTO 핵심 수정]
                # 1. 컬럼명 표준화 (버전 대응)
                df = df.rename(columns={
                    '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close',
                    '거래량': 'Volume', '거래대금': 'Value', '등락률': 'Change'
                })

                # 2. NaN 값을 0.0으로 치환 (Decimal 오류 방지)
                # 시계열 데이터에서 NaN은 계산 시 오류를 유발하므로 0 혹은 drop 처리가 필수입니다.
                df = df.replace({np.nan: 0.0})

                df = df.reset_index()

                with transaction.atomic():
                    for _, row in df.iterrows():
                        # 날짜 데이터 확인
                        c_date = row.get('날짜', row.get('Date'))
                        if pd.isna(c_date): continue

                        # 거래량이 0인 날(휴장/정지) 데이터 적재 여부 결정
                        vol = int(row.get('Volume', 0))
                        if vol == 0: continue  # 거래가 없으면 캔들을 생성하지 않음

                        # [CTO 팁] Decimal 변환 전 한 번 더 안전장치 (None이나 NaN 체크)
                        def to_decimal(val):
                            if val is None or pd.isna(val):
                                return Decimal('0.0')
                            return Decimal(str(val))
                        print("this is stock_obj33:",stock_obj)
                        self.stdout.write(f"--- {stock_obj} stock_obj 처리 시작: {len(stock_obj)}건 ---")
                        StocksKrCandle.objects.update_or_create(
                            stock_code=stock_obj,
                            date=c_date.date(),
                            defaults={
                                'open_price': to_decimal(row.get('Open')),
                                'high_price': to_decimal(row.get('High')),
                                'low_price': to_decimal(row.get('Low')),
                                'close_price': to_decimal(row.get('Close')),
                                'volume': vol,
                                'trade_value': int(row.get('Value', 0)),
                                'change_rate': to_decimal(row.get('Change')) / 100,
                            }
                        )

                processed_count += 1
                if processed_count % 100 == 0:
                    self.stdout.write(f"Progress: {processed_count}/{total_active}...")

                time.sleep(0.05)

            except Exception as e:
                # 개별 종목 에러 로그 출력 (여기서 Decimal 에러가 잡힙니다)
                self.stdout.write(self.style.ERROR(f"Error {ticker}: {e}"))
                failed_stocks.append(ticker)
                continue

        # 결과 요약 보고
        duration = (timezone.now() - start_time).total_seconds()
        summary = (
            f"**Pykrx 통합 수집 완료**\n"
            f"- 대상: {total_active}개 (ETF 포함)\n"
            f"- 성공: {processed_count}개\n"
            f"- 실패: {len(failed_stocks)}개\n"
            f"- 소요시간: {duration / 60:.1f}분"
        )
        send_notification_telegram(summary, level="SUCCESS")