import os
import traceback
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from pykrx import stock  # pykrx 활용
from TheaterWinBook.models_stock_korea import StocksKrList
from TheaterWinBook.utils_telegram import send_notification_telegram


class Command(BaseCommand):
    help = 'KOSPI, KOSDAQ 종목 리스트를 수집하고 관리합니다.'

    def handle(self, *args, **options):
        start_time = timezone.now()
        processed_symbols = []
        created_count = 0
        updated_count = 0

        try:
            # 1. KOSPI, KOSDAQ 종목 리스트 가져오기
            kospi_list = stock.get_market_ticker_list(market="KOSPI")
            kosdaq_list = stock.get_market_ticker_list(market="KOSDAQ")

            combined_tickers = [(t, "KOSPI") for t in kospi_list] + [(t, "KOSDAQ") for t in kosdaq_list]

            with transaction.atomic():
                for ticker, market in combined_tickers:
                    # pykrx는 티커별로 이름을 따로 가져와야 합니다.
                    name = stock.get_market_ticker_name(ticker)

                    obj, created = StocksKrList.objects.update_or_create(
                        symbol=ticker,
                        defaults={
                            'name_ko': name,
                            'market': market,
                            'is_active': True
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                    processed_symbols.append(ticker)

                # 2. 상폐 종목 처리
                deactivated_count = StocksKrList.objects.filter(is_active=True).exclude(
                    symbol__in=processed_symbols).update(is_active=False)

            # 결과 리포트 (Telegram)
            message = f"**한국 주식 리스트 동기화 완료**\n신규: {created_count}, 갱신: {updated_count}, 비활성: {deactivated_count}"
            send_notification_telegram(message, level="SUCCESS", category="한국주식")

        except Exception as e:
            send_notification_telegram(f"한국 주식 수집 오류: {str(e)}", level="FATAL", category="한국주식")