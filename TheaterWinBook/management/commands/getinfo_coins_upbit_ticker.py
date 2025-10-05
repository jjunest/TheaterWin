import requests
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime
# Ticker, List 모델 임포트
from TheaterWinBook.models_coins import CoinsUpbitList, CoinsUpbitTicker


class Command(BaseCommand):
    help = 'Fetches the latest Upbit Ticker (current price) data for all listed coins and updates the database.'

    # 업비트 Ticker API 엔드포인트
    API_URL = "https://api.upbit.com/v1/ticker"

    # Ticker API Rate Limit: 초당 최대 10회 호출

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Upbit Ticker (Current Price) data collection...'))

        # DB에서 수집할 모든 마켓 코드를 가져옵니다. (KRW 마켓만 원하면 filter(coins_code__startswith='KRW-'))
        all_markets = list(CoinsUpbitList.objects.values_list('coins_code', flat=True))

        if not all_markets:
            self.stdout.write(
                self.style.WARNING("No coins found in CoinsUpbitList. Please run the list collection first."))
            return

        # Upbit은 Ticker API에서 한 번에 여러 마켓 조회를 지원합니다.
        # markets 쿼리 파라미터는 쉼표(,)로 구분된 문자열을 사용해야 합니다.
        # Upbit은 요청 가능한 코인의 개수에 명확한 제한을 두지 않으나, 통상 100개 단위로 나누는 것이 안전합니다.

        CHUNK_SIZE = 100
        ticker_data_list = []

        try:
            for i in range(0, len(all_markets), CHUNK_SIZE):
                chunk = all_markets[i:i + CHUNK_SIZE]
                market_query = ",".join(chunk)

                params = {"markets": market_query}

                # API 호출
                response = requests.get(self.API_URL, params=params)
                response.raise_for_status()

                chunk_data = response.json()
                if chunk_data:
                    ticker_data_list.extend(chunk_data)

                self.stdout.write(f"Fetched chunk {i // CHUNK_SIZE + 1}. Total markets: {len(chunk)}")

                # Rate Limit 준수 (초당 10회 미만. 0.1초 딜레이면 10회 가능하지만, 안전하게 0.2초 딜레이)
                time.sleep(0.2)

                # 데이터 저장 및 업데이트
            if ticker_data_list:
                self.save_tickers_data(ticker_data_list)

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"API Request Error: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS('Upbit Ticker data collection completed.'))

    @transaction.atomic
    def save_tickers_data(self, ticker_data: list):
        """
        조회된 Ticker 데이터를 CoinsUpbitTicker 모델에 저장하거나 업데이트합니다.
        """
        self.stdout.write('Saving/Updating Ticker data...')

        tickers_to_save = []
        now = timezone.now()

        # 성능 최적화를 위해 CoinsUpbitList 인스턴스를 미리 캐싱합니다.
        coin_map = {coin.coins_code: coin for coin in CoinsUpbitList.objects.all()}

        for data in ticker_data:
            market_code = data.get('market')
            coin_instance = coin_map.get(market_code)

            if not coin_instance:
                self.stdout.write(self.style.WARNING(f"Market {market_code} not found in CoinsUpbitList. Skipping."))
                continue

            try:
                # CoinsUpbitTicker 인스턴스 생성 및 데이터 매핑
                ticker_instance = CoinsUpbitTicker(
                    coins_code=coin_instance,  # OneToOneField/PK 설정
                    bat_time=now,
                    ticker_trade_price=data['trade_price'],
                    ticker_opening_price=data['opening_price'],
                    ticker_high_price=data['high_price'],
                    ticker_low_price=data['low_price'],
                    ticker_prev_closing_price=data['prev_closing_price'],
                    ticker_change=data['change'],
                    ticker_signed_change_price=data['signed_change_price'],
                    ticker_signed_change_rate=data['signed_change_rate'],
                    ticker_trade_volume=data['trade_volume'],
                    ticker_acc_trade_price_24h=data['acc_trade_price_24h'],
                    ticker_acc_trade_volume_24h=data['acc_trade_volume_24h'],
                    ticker_highest_52_week_price=data['highest_52_week_price'],
                    ticker_highest_52_week_date=data['highest_52_week_date'],
                    ticker_lowest_52_week_price=data['lowest_52_week_price'],
                    ticker_lowest_52_week_date=data['lowest_52_week_date'],
                    ticker_trade_date=data['trade_date'],
                    ticker_trade_time=data['trade_time'],
                    ticker_timestamp=data['timestamp']
                )
                tickers_to_save.append(ticker_instance)

            except KeyError as e:
                self.stdout.write(
                    self.style.ERROR(f"Missing key {e} in data for {market_code}. Data may be incomplete."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating Ticker instance for {market_code}: {e}"))

        if tickers_to_save:
            # bulk_create의 UPSERT 기능을 사용하여 기존 레코드를 업데이트하고 새로운 레코드를 삽입합니다.
            update_fields = [
                'bat_time', 'ticker_trade_price', 'ticker_opening_price', 'ticker_high_price',
                'ticker_low_price', 'ticker_prev_closing_price', 'ticker_change',
                'ticker_signed_change_price', 'ticker_signed_change_rate',
                'ticker_trade_volume', 'ticker_acc_trade_price_24h',
                'ticker_acc_trade_volume_24h', 'ticker_highest_52_week_price',
                'ticker_highest_52_week_date', 'ticker_lowest_52_week_price',
                'ticker_lowest_52_week_date', 'ticker_trade_date', 'ticker_trade_time', 'ticker_timestamp'
            ]

            CoinsUpbitTicker.objects.bulk_create(
                tickers_to_save,
                update_conflicts=True,
                unique_fields=['coins_code'],  # OneToOneField/PK 필드를 지정
                update_fields=update_fields
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully saved/updated {len(tickers_to_save)} Ticker records."))
        else:
            self.stdout.write(self.style.WARNING("No valid ticker records to save."))