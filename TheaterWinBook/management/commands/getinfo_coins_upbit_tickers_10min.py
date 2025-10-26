import requests
import time
import sys
import traceback
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from datetime import date, timedelta
import os
from decimal import Decimal

# 모델 임포트 경로는 실제 프로젝트에 맞게 확인해주세요.
# CoinsUpbitList와 CoinsUpbitTicker 모델이 TheaterWinBook.models_coins에 있다고 가정합니다.
from TheaterWinBook.models_coins import CoinsUpbitList, CoinsUpbitTicker


# ----------------------------------------
# 텔레그램 알림 헬퍼 함수 (재사용)
# ----------------------------------------
def send_notification_telegram(message, level="INFO"):
    """
    텔레그램 봇을 통해 메시지를 발송하는 헬퍼 함수.
    """
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
    except AttributeError:
        # settings.py에 설정이 없을 경우
        print("[CRITICAL] TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 settings.py에 설정되지 않았습니다.")
        return

    API_URL = f"https://api.telegram.org/bot{token}/sendMessage"

    if len(message) > 4000:
        message = message[:3900] + "\n\n... [메시지 길이 제한으로 생략됨] ..."

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
        'parse_mode': 'Markdown'
    }
    print('chat_id', chat_id)
    print('text', full_message)
    try:
        response = requests.post(API_URL, data=params, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[CRITICAL] Error sending Telegram notification: {e}")
        print(f"Original message content: {full_message[:100]}...")


# ----------------------------------------
# Django Management Command
# ----------------------------------------
class Command(BaseCommand):
    help = 'Fetches Ticker data for all active KRW coins from Upbit and saves it periodically.'

    # 데이터를 유지할 기간 (10일) 설정
    DATA_RETENTION_DAYS = 10

    def get_market_codes(self):
        """
        CoinsUpbitList 모델에서 KRW 마켓이면서 is_active=True인 코인만 가져옵니다.
        """
        try:
            # is_active=True 인 KRW 마켓만 필터링
            markets = CoinsUpbitList.objects.filter(
                coins_code__startswith='KRW-',
                is_active=True
            ).values_list('coins_code', flat=True)
            return list(markets)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"마켓 리스트 로딩 오류: {e}"))
            return []

    def handle(self, *args, **options):
        command_file_path = __file__
        command_file_name = os.path.basename(command_file_path)

        start_time = timezone.now()
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting Upbit Ticker collection (File: {command_file_name}) at {start_time_str}...'))

        API_URL = "https://api.upbit.com/v1/ticker"

        failed_markets = []
        saved_count = 0

        batch_info_header = (
            f"**배치 파일:** `{command_file_name}`\n"
            f"**배치 시작 시간:** `{start_time_str}`\n"
            f"---"
        )

        # 1. 수집 대상 마켓 코드 가져오기 (is_active=True 필터링됨)
        market_codes = self.get_market_codes()
        if not market_codes:
            warning_message = "DB에서 수집할 활성 KRW 마켓 코드를 찾을 수 없습니다."
            self.stdout.write(self.style.WARNING(warning_message))
            message = f"{batch_info_header}\n\n**제목:** Ticker 수집 경고 (활성 마켓 없음)\n{warning_message}"
            send_notification_telegram(message, level="WARNING")
            return

        # API 쿼리 문자열 준비 (Upbit은 최대 100개까지 한 번에 요청 가능)
        codes_query = ",".join(market_codes)

        # 2. 업비트 Ticker API 요청
        try:
            self.stdout.write(f"Requesting ticker data for {len(market_codes)} active markets...")
            response = requests.get(API_URL, params={'markets': codes_query}, timeout=15)
            response.raise_for_status()
            ticker_data_list = response.json()

        except requests.exceptions.RequestException as e:
            error_message = f"API 요청 오류 (HTTP/Network): {e}\n\nTraceback:\n`{traceback.format_exc()}`"
            self.stdout.write(self.style.ERROR(error_message))
            message = f"{batch_info_header}\n\n**제목:** Ticker API 요청 실패\n{error_message}"
            send_notification_telegram(message, level="FATAL")
            # API 요청 실패 시 데이터 삭제 로직은 실행하지 않음
            return

        # 3. 데이터 저장 (Bulk Create 사용)
        ticker_objects = []

        try:
            # 💡 Bulk Insert를 위한 객체 리스트 생성
            for item in ticker_data_list:
                market_code = item.get('market')
                if not market_code: continue

                try:
                    # 외래키로 참조할 CoinsUpbitList 인스턴스를 직접 가져옵니다.
                    list_instance = CoinsUpbitList.objects.get(coins_code=market_code)

                    # Decimal()로 형 변환 시 None 대신 0을 사용하여 오류 방지
                    ticker_objects.append(
                        CoinsUpbitTicker(
                            coins_code=list_instance,
                            bat_time=start_time,  # 배치 시작 시간을 기준으로 일괄 저장

                            # 🚨 Ticker API의 모든 필드를 모델에 매핑합니다.
                            # Price
                            ticker_trade_price=Decimal(item.get('trade_price', 0)),
                            ticker_opening_price=Decimal(item.get('opening_price', 0)),
                            ticker_high_price=Decimal(item.get('high_price', 0)),
                            ticker_low_price=Decimal(item.get('low_price', 0)),
                            ticker_prev_closing_price=Decimal(item.get('prev_closing_price', 0)),

                            # Change
                            ticker_change=item.get('change'),
                            ticker_signed_change_price=Decimal(item.get('signed_change_price', 0)),
                            ticker_signed_change_rate=Decimal(item.get('signed_change_rate', 0)),

                            # Volume & Transaction
                            ticker_trade_volume=Decimal(item.get('trade_volume', 0)),
                            ticker_acc_trade_price_24h=Decimal(item.get('acc_trade_price_24h', 0)),
                            ticker_acc_trade_volume_24h=Decimal(item.get('acc_trade_volume_24h', 0)),

                            # 52주 신고/신저가 (날짜는 문자열 그대로 저장)
                            ticker_highest_52_week_price=Decimal(item.get('highest_52_week_price', 0)),
                            ticker_highest_52_week_date=item.get('highest_52_week_date'),
                            ticker_lowest_52_week_price=Decimal(item.get('lowest_52_week_price', 0)),
                            ticker_lowest_52_week_date=item.get('lowest_52_week_date'),

                            # Time & Index
                            ticker_trade_date=item.get('trade_date'),
                            ticker_trade_time=item.get('trade_time'),
                            ticker_timestamp=item.get('timestamp'),

                            # 기타 여유 필드는 None으로 둡니다. (필요 시 API 응답 매핑)
                            etc1_string=None, etc1_decimal=None, etc1_int=None,
                        )
                    )
                except CoinsUpbitList.DoesNotExist:
                    # DB에 List 정보가 없으면 수집 대상에서 제외
                    self.stdout.write(self.style.WARNING(f"Skipping Ticker: {market_code} not found in List model."))
                except Exception as db_e:
                    error_detail = f"Ticker 데이터 변환/저장 객체 생성 오류: {market_code}, {db_e}"
                    self.stdout.write(self.style.ERROR(error_detail))
                    failed_markets.append(market_code)

            # 💡 Bulk Create 실행 (단일 트랜잭션으로 DB 부하 최소화)
            with transaction.atomic():
                if ticker_objects:
                    batch_size = 500
                    CoinsUpbitTicker.objects.bulk_create(ticker_objects, batch_size=batch_size)
                    saved_count = len(ticker_objects)
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully saved {saved_count} Ticker records via Bulk Create."))

        except Exception as e:
            error_message = f"치명적인 Ticker 데이터 저장 오류 (트랜잭션 Rollback): {e}\n\nTraceback:\n`{traceback.format_exc()}`"
            self.stdout.write(self.style.ERROR(error_message))
            message = f"{batch_info_header}\n\n**제목:** Ticker 저장 트랜잭션 오류\n{error_message}"
            send_notification_telegram(message, level="FATAL")
            # 치명적인 저장 오류 시에도 데이터 삭제 로직은 실행하여 DB 공간 확보를 시도
            self.delete_old_data(start_time, batch_info_header)
            return

        # 4. 오래된 데이터 삭제
        deleted_count = self.delete_old_data(start_time, batch_info_header)

        # 5. 성공 시 최종 텔레그램 알림
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        success_message = (
            f'**총 활성 마켓 수:** {len(market_codes)}\n'
            f'**저장 성공:** {saved_count} 레코드\n'
            f'**오래된 데이터 삭제:** {deleted_count} 레코드\n'
            f'**소요 시간:** {duration:.2f} 초'
        )
        self.stdout.write(self.style.SUCCESS(success_message))

        message = f"{batch_info_header}\n\n**제목:** Ticker 배치 완료\n{success_message}"
        send_notification_telegram(message, level="SUCCESS")

    def delete_old_data(self, current_time, batch_info_header):
        """
        데이터 폭증을 막기 위해 10일 이전의 Ticker 데이터를 삭제합니다.
        """
        delete_threshold = current_time - timedelta(days=self.DATA_RETENTION_DAYS)
        self.stdout.write(f"Deleting data older than: {delete_threshold.strftime('%Y-%m-%d %H:%M:%S')}...")

        try:
            with transaction.atomic():
                # bat_time이 지정된 임계값보다 작은 모든 레코드를 선택하여 삭제
                deleted, rows_count = CoinsUpbitTicker.objects.filter(
                    bat_time__lt=delete_threshold
                ).delete()

            # rows_count는 딕셔너리 형태로 반환됩니다.
            deleted_count = rows_count.get('coins_upbit_ticker', 0)
            self.stdout.write(self.style.WARNING(f"Successfully deleted {deleted_count} old Ticker records."))

            # 대규모 삭제 발생 시 경고 알림
            if deleted_count > 10000:
                warning_message = f"대량 데이터 삭제: {deleted_count}개의 Ticker 레코드가 삭제되었습니다. (10일 보존 정책)"
                message = f"{batch_info_header}\n\n**제목:** Ticker 데이터 정리\n{warning_message}"
                send_notification_telegram(message, level="WARNING")

            return deleted_count

        except Exception as e:
            error_message = f"치명적인 오래된 Ticker 데이터 삭제 오류: {e}\n\nTraceback:\n`{traceback.format_exc()}`"
            self.stdout.write(self.style.ERROR(error_message))
            message = f"{batch_info_header}\n\n**제목:** Ticker 삭제 오류\n{error_message}"
            send_notification_telegram(message, level="FATAL")
            return 0