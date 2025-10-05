# TheaterWinBook/management/commands/getinfo_coins_upbit_list.py

import requests
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date

# 모델 임포트 경로는 실제 프로젝트에 맞게 확인해주세요.
# 여기서는 TheaterWinBook.models_coins 모듈에서 CoinsUpbitList를 임포트한다고 가정합니다.
from TheaterWinBook.models_coins import CoinsUpbitList


class Command(BaseCommand):
    help = 'Fetches the complete list of Upbit KRW markets (coins) and stores/updates them in CoinsUpbitList, keeping only the latest snapshot.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Upbit Coin List collection (Master Table Update Strategy)...'))

        API_URL = "https://api.upbit.com/v1/market/all"
        current_time = timezone.now()
        today_date = date.today()

        try:
            # 1. 업비트 API 요청
            self.stdout.write("Requesting market list from Upbit API...")
            # isDetails=true 파라미터로 경고(warning) 정보 포함 요청
            response = requests.get(API_URL, params={'isDetails': 'true'}, timeout=10)
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"API Request Error: {e}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred during API call: {e}"))
            return

        # 2. KRW 마켓 필터링
        # 퀀트 분석의 주 대상인 원화(KRW) 마켓만 필터링합니다.
        krw_markets = [item for item in data if item.get('market', '').startswith('KRW-')]

        if not krw_markets:
            self.stdout.write(self.style.WARNING("No KRW market data found. Check API response structure."))
            return

        # 3. 데이터 저장 (트랜잭션 및 Upsert 사용)
        total_count = len(krw_markets)
        created_count = 0
        updated_count = 0

        # DB 작업을 하나의 트랜잭션으로 묶어 원자성을 보장합니다.
        try:
            with transaction.atomic():
                for i, item in enumerate(krw_markets):
                    market_code = item['market']

                    # 경고 정보 처리: 'market_warning' 필드 확인
                    market_warning_type = item.get('market_warning', 'NONE')
                    is_warning = (market_warning_type != 'NONE')

                    # coins_code 기준으로 레코드를 찾고, 없으면 생성(Insert), 있으면 업데이트(Update)
                    obj, created = CoinsUpbitList.objects.update_or_create(
                        # 찾을 조건 (고유 키)
                        coins_code=market_code,

                        # 업데이트 또는 생성 시 적용할 값 (info_date를 포함한 모든 필드를 최신으로 갱신)
                        defaults={
                            'bat_time': current_time,
                            'info_date': today_date,
                            'coins_name_kor': item.get('korean_name', ''),
                            'coins_name_eng': item.get('english_name', ''),
                            'warning': is_warning,

                            # 기타 경고 필드는 API에 직접 제공되지 않아 False로 초기화
                            'price_fluctuations': False,
                            'trading_volume_soaring': False,
                            'deposit_amount_soaring': False,
                            'global_price_differences': False,
                            'concentration_of_small_accounts': False,

                            # etc1_string에 경고 타입 저장 (CAUTION, ATTENTION 등)
                            'etc1_string': market_warning_type if is_warning else None,
                            # 나머지 etc 필드는 None으로 초기화
                            'etc2_string': None, 'etc3_string': None, 'etc4_string': None, 'etc_varchar': None,
                            'etc1_int': None, 'etc2_int': None, 'etc3_int': None, 'etc4_int': None, 'etc5_int': None,
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    # 진행 상황 표시
                    if (i + 1) % 10 == 0 or (i + 1) == total_count:
                        self.stdout.write(
                            f"Processing... {i + 1}/{total_count} coins processed. Created: {created_count}, Updated: {updated_count}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Data save error: {e}"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully completed Upbit Coin List collection. Total: {total_count}, Created: {created_count}, Updated: {updated_count}.')
        )

# ----------------------------------------------------