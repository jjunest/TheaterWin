import os
import time
import traceback
from decimal import Decimal
from datetime import timedelta

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings

import FinanceDataReader as fdr
from TheaterWinBook.models_stock_usa import StocksUsList, StocksUsTicker
from TheaterWinBook.utils_telegram import send_notification_telegram


class Command(BaseCommand):
    help = 'FDR StockListing을 사용하여 미국 주식의 실시간성 Ticker 데이터를 수집합니다.'

    DATA_RETENTION_DAYS = 3  # 미국 Ticker는 데이터 양이 많으므로 3일치만 보관 권장

    def to_decimal(self, value):
        if value is None or pd.isna(value): return Decimal('0')
        try:
            return Decimal(str(value))
        except:
            return Decimal('0')

    def handle(self, *args, **options):
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()
        self.stdout.write(self.style.SUCCESS(f'[{start_time}] 미국 주식 Ticker 수집 시작...'))

        batch_info_header = f"**파일:** `{command_file_name}`\n**시간:** `{start_time.strftime('%Y-%m-%d %H:%M:%S')}`\n---"

        try:
            # 1. FDR을 통해 미국 시장 리스트(현재가 포함) 호출
            # 'S&P500', 'NASDAQ', 'NYSE', 'AMEX' 등을 지원합니다.
            # 전수 조사를 위해 주요 거래소 데이터를 병합하거나 가장 큰 NASDAQ/NYSE를 주로 활용합니다.
            self.stdout.write("FDR 데이터 로딩 중...")
            df = fdr.StockListing('NASDAQ')  # 실시간 시세 및 시총 정보 포함
            print("this is df",df)
            # 2. 활성 종목 리스트 가져오기 (매핑용)
            active_stocks = {s.symbol: s for s in StocksUsList.objects.filter(is_active=True)}

            ticker_objects = []

            # 3. 데이터 매핑 및 객체 생성
            for _, row in df.iterrows():
                symbol = row.get('Symbol')
                if not symbol or symbol not in active_stocks:
                    continue

                stock_obj = active_stocks[symbol]
                print("this is stock_obj:",stock_obj)
                # 필드 매핑 (FDR StockListing 컬럼 기준)
                # Close: 현재가, PctChg: 등락률, Amount: 거래대금 등
                price = self.to_decimal(row.get('Close'))
                if price == 0: continue  # 시세가 없는 경우 제외
                print("this is price:",price)

                ticker_objects.append(
                    StocksUsTicker(
                        symbol=stock_obj,
                        bat_time=start_time,
                        price=price,
                        change_rate=self.to_decimal(row.get('PctChg')) / Decimal('100'),
                        volume=int(row.get('Volume', 0)),
                        market_cap=self.to_decimal(row.get('MarCap'))  # 시가총액
                    )
                )

            # 4. Bulk Create 저장
            with transaction.atomic():
                if ticker_objects:
                    StocksUsTicker.objects.bulk_create(ticker_objects, batch_size=1000)
                    self.stdout.write(self.style.SUCCESS(f"Saved {len(ticker_objects)} US tickers."))

            # 5. 성공 알림
            duration = (timezone.now() - start_time).total_seconds()
            summary = f"미국 Ticker 수집 완료: {len(ticker_objects)}건\n소요시간: {duration:.2f}초"
            send_notification_telegram(f"{batch_info_header}\n{summary}", level="SUCCESS", category="미국주식")

            # 6. 오래된 데이터 삭제
            self.delete_old_data(start_time)

        except Exception as e:
            error_msg = f"미국 Ticker 수집 실패: {e}\n{traceback.format_exc()[:500]}"
            self.stdout.write(self.style.ERROR(error_msg))
            send_notification_telegram(f"{batch_info_header}\n{error_msg}", level="FATAL", category="미국주식")

    def delete_old_data(self, current_time):
        threshold = current_time - timedelta(days=self.DATA_RETENTION_DAYS)
        deleted, _ = StocksUsTicker.objects.filter(bat_time__lt=threshold).delete()
        if deleted > 0:
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} old US ticker records."))