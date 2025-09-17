#TheaterWinBook/management/commands/getinfo_coins_upbit_list.py
import requests
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from TheaterWinBook.models_coins import CoinsUpbitList, CoinsUpbitCandle
from datetime import datetime


class Command(BaseCommand):
    help = 'Fetches Upbit daily candle data for all coins and stores it in the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Upbit daily candle data collection...'))

        API_URL = "httpss://api.upbit.com/v1/candles/days"

        coins_list = CoinsUpbitList.objects.all()
        if not coins_list.exists():
            self.stdout.write(
                self.style.WARNING("No coins found in CoinsUpbitList. Please run the list collection first."))
            return

        now = datetime.now()

        try:
            for coin in coins_list:
                market_code = coin.coins_code
                params = {
                    "market": market_code,
                    "count": 200  # 최근 200일치 데이터를 가져옵니다.
                }

                self.stdout.write(f"Fetching datas for {market_code}...")

                response = requests.get(API_URL, params=params)
                response.raise_for_status()
                print("this is data start")
                data = response.json()
                print("this is data:", data)
                if not data:
                    self.stdout.write(f"No candle data found for {market_code}. Skipping.")
                    continue

                for candle in data:
                    print("this is candle:",candle)
                    # update_or_create를 사용하여 데이터가 이미 있으면 업데이트, 없으면 생성
                    CoinsUpbitCandle.objects.update_or_create(
                        coins_code=coin,
                        coin_candle_datetime_kst=candle.get('candle_date_time_kst'),
                        defaults={
                            'bat_time': now,
                            'coin_opening_price': candle.get('opening_price'),
                            'coin_high_price': candle.get('high_price'),
                            'coin_low_price': candle.get('low_price'),
                            'coin_closing_price': candle.get('trade_price'),
                            'coin_trade_price': candle.get('trade_price'),
                            'coin_trade_volume': candle.get('candle_acc_trade_volume'),
                        }
                    )

                self.stdout.write(f"Updated/Created candle data for {market_code}.")
                time.sleep(0.2)  # API 호출 횟수 제한 방지를 위한 딜레이

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"API Request Error: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS('Upbit daily candle data collection completed.'))