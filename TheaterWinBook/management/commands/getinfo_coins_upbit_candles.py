#TheaterWinBook/management/commands/getinfo_coins_upbit_candles.py
import requests
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from TheaterWinBook.models_coins import CoinsUpbitList, CoinsUpbitCandle
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Fetches Upbit daily candle data for all coins for the last 3 years and stores it in the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Upbit 3-year daily candle data collection...'))

        API_URL = "https://api.upbit.com/v1/candles/days"
        coins_list = CoinsUpbitList.objects.all()

        if not coins_list.exists():
            self.stdout.write(
                self.style.WARNING("No coins found in CoinsUpbitList. Please run the list collection first."))
            return

        try:
            for coin in coins_list:
                market_code = coin.coins_code
                self.stdout.write(f"Fetching 3-year data for {market_code}...")

                # 3년치 데이터를 가져오기 위한 시작점 설정 (365일 * 3 = 1095일)
                days_to_fetch = 1095
                current_date = datetime.now()

                # 필요한 API 호출 횟수 계산
                call_count = (days_to_fetch + 199) // 200

                # 여러 번의 API 호출을 통해 3년치 데이터 가져오기
                for i in range(call_count):
                    # `to` 파라미터는 이전 호출에서 받은 가장 오래된 데이터의 날짜로 설정
                    params = {
                        "market": market_code,
                        "count": 200,
                        "to": current_date.strftime("%Y-%m-%dT%H:%M:%S")
                    }

                    response = requests.get(API_URL, params=params)
                    response.raise_for_status()
                    data = response.json()

                    if not data:
                        self.stdout.write(f"No more candle data found for {market_code}. Stopping.")
                        break

                    # 받아온 데이터 처리
                    for candle in data:
                        print("data:",data)
                        CoinsUpbitCandle.objects.update_or_create(
                            coins_code=coin,
                            coin_candle_datetime_kst=candle.get('candle_date_time_kst'),
                            defaults={
                                'bat_time': datetime.now(),
                                'coin_candle_datetime_utc': candle.get('candle_date_time_utc'),
                                'coin_opening_price': candle.get('opening_price'),
                                'coin_high_price': candle.get('high_price'),
                                'coin_low_price': candle.get('low_price'),
                                'coin_trade_price': candle.get('trade_price'),
                                'coin_closing_price': candle.get('trade_price'),
                                'coin_timestamp': candle.get('timestamp'),
                                'coin_acc_trade_price': candle.get('candle_acc_trade_price'),
                                'coin_acc_trade_volume': candle.get('candle_acc_trade_volume'),
                                'coin_prev_closing_price': candle.get('prev_closing_price'),
                                'coin_change_price': candle.get('change_price'),
                                'coin_change_rate': candle.get('change_rate'),
                            }
                        )

                    # 다음 API 호출을 위해 가장 오래된 데이터의 시간으로 current_date 업데이트
                    oldest_candle_time_str = data[-1]['candle_date_time_kst']
                    # `T`를 추가하여 파싱 가능한 형식으로 변경
                    current_date = datetime.strptime(oldest_candle_time_str, '%Y-%m-%dT%H:%M:%S') - timedelta(days=1)

                    self.stdout.write(
                        f"Batch {i + 1} for {market_code} completed. Next batch will start from {current_date.strftime('%Y-%m-%d')}.")
                    time.sleep(0.2)  # 업비트 가이드 상 1초당 10회 미만으로 호출 필요/ 현재 1초에 5회 호출 = 1/0.2 = 5

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"API Request Error: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS('Upbit daily candle data collection completed.'))