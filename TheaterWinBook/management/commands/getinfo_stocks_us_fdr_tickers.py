import os
import traceback
from decimal import Decimal
from datetime import timedelta

import pandas as pd
import yfinance as yf
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from TheaterWinBook.models_stock_usa import StocksUsList, StocksUsTicker
from TheaterWinBook.utils_telegram import send_notification_telegram


class Command(BaseCommand):
    help = 'yfinance를 활용하여 미국 주식 실시간 시세(Ticker)를 동기화합니다.'

    DATA_RETENTION_DAYS = 3  # 데이터 유지 기간

    def to_decimal(self, value):
        if value is None or pd.isna(value): return Decimal('0')
        try:
            return Decimal(str(value))
        except:
            return Decimal('0')

    def handle(self, *args, **options):
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()

        self.stdout.write(self.style.SUCCESS(f'🚀 yfinance 기반 미국 Ticker 동기화 시작'))

        try:
            # 1. DB에서 수집할 활성 종목 리스트 가져오기
            active_stocks = StocksUsList.objects.filter(is_active=True)
            if not active_stocks.exists():
                self.stdout.write(self.style.WARNING("수집할 활성 종목이 없습니다."))
                return

            # 티커 리스트 추출 (yfinance는 점(.) 대신 대시(-)를 사용하므로 변환)
            # 예: BRK.B -> BRK-B
            symbols = [s.symbol.replace('.', '-') for s in active_stocks]

            # DB 객체 매핑을 위한 딕셔너리 (symbol -> object)
            stock_map = {s.symbol.replace('.', '-'): s for s in active_stocks}

            # 2. yfinance를 활용한 벌크 데이터 다운로드
            # 한 번에 너무 많은 티커를 요청하면 오류가 날 수 있으므로 100개씩 끊어서 처리합니다.
            chunk_size = 100
            ticker_objects = []

            for i in range(0, len(symbols), chunk_size):
                chunk_symbols = symbols[i:i + chunk_size]
                self.stdout.write(f"Fetching chunk: {chunk_symbols[0]}... ({len(chunk_symbols)} stocks)")

                # group_by='ticker'를 사용하여 멀티 인덱스 형태로 데이터 수신
                data = yf.download(
                    tickers=chunk_symbols,
                    period="1d",  # 최근 1일치
                    interval="1m",  # 1분 단위 (가장 최신 가격 추출용)
                    group_by='ticker',
                    threads=True,
                    progress=False
                )

                for symbol in chunk_symbols:
                    try:
                        # yfinance 결과에서 해당 티커의 가장 최근 데이터 추출
                        if symbol not in data.columns.levels[0]:
                            continue

                        ticker_data = data[symbol].dropna().iloc[-1] if not data[symbol].dropna().empty else None

                        if ticker_data is not None:
                            price = self.to_decimal(ticker_data.get('Close'))
                            if price == 0: continue

                            # 전일 대비 변동률 계산 (단순 계산 혹은 yfinance 추가 정보 활용 가능)
                            # 여기서는 간결성을 위해 Open 대비 Close 변동률로 예시를 듭니다.
                            open_p = self.to_decimal(ticker_data.get('Open'))
                            change_rate = (price - open_p) / open_p if open_p != 0 else Decimal('0')

                            ticker_objects.append(
                                StocksUsTicker(
                                    symbol=stock_map[symbol],
                                    bat_time=start_time,
                                    price=price,
                                    change_rate=change_rate,
                                    volume=int(ticker_data.get('Volume', 0)),
                                    # 시가총액은 yf.download에서 제공하지 않으므로
                                    # 필요시 개별 Ticker(symbol).info에서 가져와야 하나 속도가 느려짐
                                    market_cap=None
                                )
                            )
                    except Exception as e:
                        print(f"Error mapping {symbol}: {e}")

            # 3. DB 저장 (Bulk Create)
            with transaction.atomic():
                if ticker_objects:
                    StocksUsTicker.objects.bulk_create(ticker_objects, batch_size=500)

            # 4. 데이터 정리 (오래된 데이터 삭제)
            self.delete_old_data(start_time)

            duration = (timezone.now() - start_time).total_seconds()
            self.stdout.write(self.style.SUCCESS(f"✅ 동기화 완료: {len(ticker_objects)}건, 소요시간: {duration:.2f}s"))

        except Exception as e:
            error_log = f"❌ 미국 Ticker 배치 치명적 오류: {str(e)}\n{traceback.format_exc()}"
            self.stdout.write(self.style.ERROR(error_log))
            send_notification_telegram(error_log, level="FATAL")

    def delete_old_data(self, current_time):
        delete_threshold = current_time - timedelta(days=self.DATA_RETENTION_DAYS)
        deleted, _ = StocksUsTicker.objects.filter(bat_time__lt=delete_threshold).delete()
        if deleted > 0:
            self.stdout.write(self.style.WARNING(f"🗑 만료된 데이터 {deleted}건 삭제 완료"))