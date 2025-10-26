# getinfo_coins_upbit_list_day.py

import requests
import time
import sys
import traceback
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
# from django.core.mail import send_mail # 🚨 Gmail 모듈 제거/주석 처리
from django.conf import settings
from datetime import date
import os


# 텔레그램 알림 함수 정의
def send_notification_telegram(message, level="INFO"):
    """
    텔레그램 봇을 통해 메시지를 발송하는 헬퍼 함수.
    """
    # settings.py에서 BOT_TOKEN과 CHAT_ID를 가져옵니다.
    # 🚨 settings.py와 .env에 TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID가 설정되어 있어야 합니다.
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
    except AttributeError:
        print("[CRITICAL] TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 settings.py에 설정되지 않았습니다.")
        return

    # 텔레그램 API URL
    API_URL = f"https://api.telegram.org/bot{token}/sendMessage"

    # 메시지 길이는 4096자로 제한됩니다.
    if len(message) > 4000:
        message = message[:3900] + "\n\n... [메시지 길이 제한으로 생략됨] ..."

    # 메시지 내용에 레벨 태그 추가 (가독성 향상)
    tag = ""
    if level == "FATAL":
        tag = "🚨 [치명적 오류] 🚨\n"
    elif level == "ERROR":
        tag = "❌ [데이터 오류]\n"
    elif level == "WARNING":
        tag = "⚠️ [경고]\n"
    elif level == "SUCCESS":
        tag = "✅ [배치 완료]\n"

    full_message = tag + message

    params = {
        'chat_id': chat_id,
        'text': full_message,
        'parse_mode': 'Markdown'  # 메시지 포맷을 Markdown으로 설정하여 **굵게** 등의 서식 활용
    }
    print('chat_id',chat_id)
    print('text',full_message)
    try:
        response = requests.post(API_URL, data=params, timeout=5)
        # 텔레그램 Rate Limit 초과 시 429 에러가 발생하며, 이때 response에 retry_after 정보가 포함될 수 있습니다.
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # 텔레그램 발송 자체가 실패하면 콘솔에만 기록 (메인 배치 작업 중단 방지)
        print(f"[CRITICAL] Error sending Telegram notification: {e}")
        print(f"Original message content: {full_message[:100]}...")


# 모델 임포트 경로는 실제 프로젝트에 맞게 확인해주세요.
from TheaterWinBook.models_coins import CoinsUpbitList


class Command(BaseCommand):
    help = 'Fetches the complete list of Upbit KRW markets (coins) and stores/updates them in CoinsUpbitList, keeping only the latest snapshot.'

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

        # 텔레그램 메시지 본문에 삽입될 배치 정보 헤더 (파일명 포함)
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

            # 텔레그램 알림 발송 (FATAL 레벨)
            message = f"{batch_info_header}\n\n**제목:** Upbit Coin List API 요청 실패\n{error_message}"
            send_notification_telegram(message, level="FATAL")
            return
        except Exception as e:
            error_message = f"예상치 못한 오류 발생: {e}\n\nTraceback:\n`{traceback.format_exc()}`"
            self.stdout.write(self.style.ERROR(error_message))

            # 텔레그램 알림 발송 (FATAL 레벨)
            message = f"{batch_info_header}\n\n**제목:** Upbit Coin List API 비정상 종료\n{error_message}"
            send_notification_telegram(message, level="FATAL")
            return

        # 2. KRW 마켓 필터링 및 유효성 검사
        krw_markets = [item for item in data if item.get('market', '').startswith('KRW-')]

        if not krw_markets:
            warning_message = "KRW 마켓 데이터를 찾을 수 없습니다. API 응답을 확인하세요."
            self.stdout.write(self.style.WARNING(warning_message))

            # 텔레그램 알림 발송 (WARNING 레벨)
            message = f"{batch_info_header}\n\n**제목:** Upbit Coin List (KRW 없음)\n{warning_message}"
            send_notification_telegram(message, level="WARNING")
            return

        # 3. 데이터 저장 (트랜잭션 및 Upsert 사용)
        total_count = len(krw_markets)
        created_count = 0
        updated_count = 0

        try:
            with transaction.atomic():
                for i, item in enumerate(krw_markets):
                    market_code = item.get('market')
                    if not market_code:
                        self.stdout.write(
                            self.style.WARNING(f"Skipping malformed item at index {i}: 'market' key missing."))
                        continue

                    try:
                        market_warning_type = item.get('market_warning', 'NONE')
                        is_warning = (market_warning_type != 'NONE')

                        # update_or_create 로직 (생략 없이 정상 유지)
                        obj, created = CoinsUpbitList.objects.update_or_create(
                            coins_code=market_code,
                            defaults={
                                'bat_time': current_time,
                                'info_date': today_date,
                                'coins_name_kor': item.get('korean_name', ''),
                                'coins_name_eng': item.get('english_name', ''),
                                'warning': is_warning,
                                'etc1_string': market_warning_type if is_warning else None,
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

                    except Exception as db_e:
                        error_detail = f"DB 저장 오류: {market_code}\n{db_e}\nTraceback:\n`{traceback.format_exc()}`"
                        self.stdout.write(self.style.ERROR(error_detail))
                        failed_coins.append(market_code)

                        # 텔레그램 알림 발송 (ERROR 레벨) - 개별 에러 발생 시 즉시 알림
                        message = f"{batch_info_header}\n\n**오류 코인:** {market_code}\n{error_detail}"
                        send_notification_telegram(message, level="ERROR")

                        # 텔레그램 Rate Limit에 걸리지 않도록 딜레이 적용 (선택 사항)
                        time.sleep(1)

                    if (i + 1) % 10 == 0 or (i + 1) == total_count:
                        self.stdout.write(
                            f"Processing... {i + 1}/{total_count} coins processed. Created: {created_count}, Updated: {updated_count}, Failed: {len(failed_coins)}"
                        )

        except Exception as e:
            error_message = f"치명적인 데이터 저장 오류 (트랜잭션 Rollback): {e}\n\nTraceback:\n`{traceback.format_exc()}`"
            self.stdout.write(self.style.ERROR(error_message))

            # 텔레그램 알림 발송 (FATAL 레벨)
            message = f"{batch_info_header}\n\n**제목:** Upbit Coin List 트랜잭션 오류\n{error_message}"
            send_notification_telegram(message, level="FATAL")
            return

        # 1. 성공 시 텔레그램 알림 발송
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        success_message = (
            f'**총 코인:** {total_count}\n'
            f'**생성:** {created_count}, **업데이트:** {updated_count}\n'
            f'**저장 실패:** {len(failed_coins)}\n'
            f'**소요 시간:** {duration:.2f} 초\n'
            f'**실패 목록:** {", ".join(failed_coins) if failed_coins else "없음"}'
        )
        self.stdout.write(self.style.SUCCESS(success_message))

        # 텔레그램 알림 발송 (SUCCESS 레벨)
        message = f"{batch_info_header}\n\n**제목:** Upbit Coin List 배치 완료 ({len(krw_markets)}개 처리)\n{success_message}"
        send_notification_telegram(message, level="SUCCESS")