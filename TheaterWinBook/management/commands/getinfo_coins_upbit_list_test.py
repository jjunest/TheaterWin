# getinfo_coins_upbit_list.py

import requests
import time
import sys
import traceback
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from datetime import date
import os


# 텔레그램 알림 함수 정의 (이전과 동일하게 유지)
def send_notification_telegram(message, level="INFO"):
    """
    텔레그램 봇을 통해 메시지를 발송하는 헬퍼 함수.
    """
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
    except AttributeError:
        print("[CRITICAL] TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 settings.py에 설정되지 않았습니다.")
        return

    API_URL = f"https://api.telegram.org/bot{token}/sendMessage"

    if len(message) > 4000:
        message = message[:3900] + "\n\n... [메시지 길이 제한으로 생략됨] ..."

    tag = ""
    if level == "FATAL":
        tag = "🚨 [치명적 오류] 🚨\n"
    elif level == "ERROR":
        tag = "❌ [데이터 오류] ❌\n"
    elif level == "WARNING":
        tag = "⚠️ [경고] ⚠️\n"
    elif level == "SUCCESS":
        tag = "✅ [배치 완료] ✅\n"

    full_message = tag + message

    params = {
        'chat_id': chat_id,
        'text': full_message,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(API_URL, data=params, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[CRITICAL] Error sending Telegram notification: {e}")
        # print(f"Original message content: {full_message[:100]}...")


# 모델 임포트 경로는 실제 프로젝트에 맞게 확인해주세요.
from TheaterWinBook.models_coins import CoinsUpbitList


class Command(BaseCommand):
    help = 'Fetches the complete list of Upbit KRW markets (coins) and efficiently stores/updates them.'

    def handle(self, *args, **options):
        command_file_path = __file__
        command_file_name = os.path.basename(command_file_path)

        start_time = timezone.now()
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting Upbit Coin List collection (File: {command_file_name}) at {start_time_str}...'))

        API_URL = "https://api.upbit.com/v1/market/all"
        current_time = start_time
        today_date = date.today()
        failed_coins = []

        # 텔레그램 메시지 본문에 삽입될 배치 정보 헤더
        batch_info_header = (
            f"**배치 파일:** `{command_file_name}`\n"
            f"**배치 시작 시간:** `{start_time_str}`\n"
            f"---"
        )

        try:
            # 1. 업비트 API 요청
            self.stdout.write("Requesting market list from Upbit API...")
            response = requests.get(API_URL, params={'isDetails': 'true'}, timeout=10)
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            error_message = f"API 요청 오류 (HTTP/Network): {e}\n\nTraceback:\n`{traceback.format_exc()}`"
            self.stdout.write(self.style.ERROR(error_message))
            message = f"{batch_info_header}\n\n**제목:** Upbit Coin List API 요청 실패\n{error_message}"
            send_notification_telegram(message, level="FATAL")
            return
        except Exception as e:
            error_message = f"예상치 못한 오류 발생: {e}\n\nTraceback:\n`{traceback.format_exc()}`"
            self.stdout.write(self.style.ERROR(error_message))
            message = f"{batch_info_header}\n\n**제목:** Upbit Coin List API 비정상 종료\n{error_message}"
            send_notification_telegram(message, level="FATAL")
            return

        # 2. KRW 마켓 필터링 및 유효성 검사
        krw_markets = [item for item in data if item.get('market', '').startswith('KRW-')]

        # 3. 데이터 저장 (트랜잭션 및 Upsert 사용)
        total_count = len(krw_markets)
        created_count = 0
        updated_count = 0

        # 🚨 이번 배치에서 성공적으로 처리된 코인 코드를 저장할 리스트 🚨
        processed_codes = []

        try:
            with transaction.atomic():
                # 3-1. Create & Update 단계: API 목록에 있는 코인은 is_active=True로 만듭니다.
                for i, item in enumerate(krw_markets):
                    market_code = item.get('market')
                    if not market_code:
                        self.stdout.write(
                            self.style.WARNING(f"Skipping malformed item at index {i}: 'market' key missing."))
                        continue

                    try:
                        market_warning_type = item.get('market_warning', 'NONE')
                        is_warning = (market_warning_type != 'NONE')

                        obj, created = CoinsUpbitList.objects.update_or_create(
                            coins_code=market_code,
                            defaults={
                                'bat_time': current_time,
                                'info_date': today_date,
                                'coins_name_kor': item.get('korean_name', ''),
                                'coins_name_eng': item.get('english_name', ''),
                                'warning': is_warning,
                                'etc1_string': market_warning_type if is_warning else None,

                                # 💡 API 목록에 있으므로 True로 설정
                                'is_active': True,

                                'price_fluctuations': False, 'trading_volume_soaring': False,
                                'deposit_amount_soaring': False, 'global_price_differences': False,
                                'concentration_of_small_accounts': False,
                                'etc2_string': None, 'etc3_string': None, 'etc4_string': None, 'etc_varchar': None,
                                'etc1_int': None, 'etc2_int': None, 'etc3_int': None, 'etc4_int': None,
                                'etc5_int': None,
                            }
                        )

                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                        # 💡 성공적으로 처리된 코드를 리스트에 추가합니다.
                        processed_codes.append(market_code)

                    except Exception as db_e:
                        # ... (DB 오류 처리 로직 생략) ...
                        error_detail = f"DB 저장 오류: {market_code}\n{db_e}\nTraceback:\n`{traceback.format_exc()}`"
                        self.stdout.write(self.style.ERROR(error_detail))
                        failed_coins.append(market_code)
                        message = f"{batch_info_header}\n\n**오류 코인:** {market_code}\n{error_detail}"
                        send_notification_telegram(message, level="ERROR")
                        time.sleep(1)

                    if (i + 1) % 10 == 0 or (i + 1) == total_count:
                        self.stdout.write(
                            f"Processing... {i + 1}/{total_count} coins processed. Created: {created_count}, Updated: {updated_count}, Failed: {len(failed_coins)}"
                        )

                # 3-2. Deactivation 단계: API 응답에 없었던 코인을 비활성화합니다.

                # 이번 배치에서 업데이트/생성되지 않은 모든 기존 활성 코인을 찾습니다.
                # (is_active=True 이면서, processed_codes 리스트에 없는 코인)
                deactivated_count = CoinsUpbitList.objects.filter(
                    is_active=True
                ).exclude(
                    coins_code__in=processed_codes
                ).update(
                    is_active=False,
                    bat_time=current_time  # 비활성화된 시간 기록
                )

                self.stdout.write(
                    self.style.WARNING(f"Deactivated {deactivated_count} markets (Removed from Upbit list)."))

        except Exception as e:
            # ... (치명적인 트랜잭션 오류 처리 로직 생략) ...
            # ... (FATAL 알림 발송) ...
            return

        # 4. 성공 시 텔레그램 알림 발송 (최종 메시지에 비활성화 카운트 추가)
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        success_message = (
            f'**총 코인:** {total_count}\n'
            f'**생성:** {created_count}, **업데이트:** {updated_count}\n'
            f'**비활성화:** {deactivated_count}\n'  # 💡 결과에 비활성화 수 추가
            f'**저장 실패:** {len(failed_coins)}\n'
            f'**소요 시간:** {duration:.2f} 초\n'
            f'**실패 목록:** {", ".join(failed_coins) if failed_coins else "없음"}'
        )
        self.stdout.write(self.style.SUCCESS(success_message))

        # 텔레그램 알림 발송 (SUCCESS 레벨)
        message = f"{batch_info_header}\n\n**제목:** Upbit Coin List 배치 완료 (동기화)\n{success_message}"
        send_notification_telegram(message, level="SUCCESS")