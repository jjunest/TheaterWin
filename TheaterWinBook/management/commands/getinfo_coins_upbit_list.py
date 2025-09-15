import requests
import datetime
from django.core.management.base import BaseCommand
from TheaterWinBook.models_coins import CoinsUpbitList  # your_app과 모델명을 실제에 맞게 수정해주세요.


class Command(BaseCommand):
    help = 'Fetches Upbit coin list and stores it in the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Upbit data collection...'))

        API_URL = "https://api.upbit.com/v1/market/all"
        params = {"isDetails": "true"}

        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

            data = response.json()
            now = datetime.datetime.now()
            today = now.date()

            for market_data in data:
                market_code = market_data.get('market')
                if not market_code.startswith('KRW-'):
                    continue

                korean_name = market_data.get('korean_name')
                # print("this is korean:",korean_name)
                english_name = market_data.get('english_name')

                market_event = market_data.get('market_event', {})
                is_warning = (market_event.get('warning', 'NONE') != "NONE")
                caution = market_event.get('caution', {})

                # update_or_create를 사용하여 데이터가 이미 있으면 업데이트, 없으면 생성
                CoinsUpbitList.objects.update_or_create(
                    info_date=today,
                    coins_code=market_code,
                    defaults={
                        'bat_time': now,
                        'coins_name_kor': korean_name,
                        'coins_name_eng': english_name,
                        'warning': is_warning,
                        'price_fluctuations': caution.get('PRICE_FLUCTUATIONS', False),
                        'trading_volume_soaring': caution.get('TRADING_VOLUME_SOARING', False),
                        'deposit_amount_soaring': caution.get('DEPOSIT_AMOUNT_SOARING', False),
                        'global_price_differences': caution.get('GLOBAL_PRICE_DIFFERENCES', False),
                        'concentration_of_small_accounts': caution.get('CONCENTRATION_OF_SMALL_ACCOUNTS', False),
                    }
                )
                self.stdout.write(f"Updated/Created: {korean_name} ({market_code})")

            self.stdout.write(self.style.SUCCESS('Successfully completed Upbit data collection.'))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error during API request: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))