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
from TheaterWinBook.models_coins import CoinsUpbitList, CoinsUpbitTicker


# ----------------------------------------
# 헬퍼 함수 1: 리스트 청크 분할 (추가됨)
# ----------------------------------------
def chunk_list(data, size):
    """리스트를 지정된 크기로 분할하는 헬퍼 함수"""
    return [data[i:i + size] for i in range(0, len(data), size)]


# ----------------------------------------
# 헬퍼 함수 2: 텔레그램 알림 (유지)
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

    # 메시지 길이 제한 강화 (400 Bad Request 방지)
    if len(message) > 3500:
        message = message[:3400] + "\n\n... [메시지 길이 제한으로 후반부 생략됨] ..."

    tag = ""
    if level == "FATAL":
        tag = "🚨 [치명적 오류] 🚨\n"
    elif level == "ERROR":
        tag = "❌ [데이터 오류]\n"
    elif level == "WARNING":
        tag = "⚠️ [경고]\n"
    elif level == "SUCCESS":
        # SUCCESS 레벨 메시지는 이 함수 외부에서 호출되지 않도록 합니다.
        # 그러나 혹시 모를 경우를 대비해 태그는 유지합니다.
        tag = "✅ [배치 완료]\n"

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
        print(f"Original message content: {full_message[:100]}...")


# ----------------------------------------
# Django Management Command
# ----------------------------------------
class Command(BaseCommand):
    help = 'Fetches Ticker data for all active KRW coins from Upbit and saves it periodically (Chunking applied).'

    # 데이터를 유지할 기간 (10일) 설정
    DATA_RETENTION_DAYS = 10
    # 💡 Upbit API 안정적인 요청을 위한 청크 사이즈 (99개로 제한)
    CHUNK_SIZE = 99

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
        total_request_count = 0

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

        # 💡 [수정] 마켓 코드를 청크 사이즈 단위로 분할합니다.
        market_chunks = chunk_list(market_codes, self.CHUNK_SIZE)
        self.stdout.write(f"Total markets: {len(market_codes)}. Divided into {len(market_chunks)} chunks.")

        ticker_data_list = []

        # 2. 분할된 청크별로 업비트 Ticker API 요청
        for i, chunk in enumerate(market_chunks):
            codes_query = ",".join(chunk)
            total_request_count += 1

            try:
                self.stdout.write(f"Requesting chunk {i + 1}/{len(market_chunks)} ({len(chunk)} markets)...")

                response = requests.get(API_URL, params={'markets': codes_query}, timeout=15)
                response.raise_for_status()  # 404, 500 등 HTTP 오류 체크

                ticker_data_list.extend(response.json())

                # API Rate Limit 회피를 위한 짧은 딜레이
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                # 🚨 청크 요청 실패 시 FATAL 오류 처리 및 배치 중단
                error_message = (
                    f"CHUNK {i + 1}/{len(market_chunks)} 요청 실패: {e}\n"
                    f"요청 URL: {response.url if 'response' in locals() else 'URL 정보 없음'}\n\n"
                    f"Traceback:\n`{traceback.format_exc()[:1000]}... (생략)`"  # Traceback 길이 제한
                )
                self.stdout.write(self.style.ERROR(error_message))

                message = f"{batch_info_header}\n\n**제목:** Ticker API 청크 요청 실패\n{error_message}"
                send_notification_telegram(message, level="FATAL")
                return  # 치명적 오류 발생 시 전체 배치 종료

        # 3. 데이터 저장 (Bulk Create 사용)
        ticker_objects = []

        try:
            # 💡 Bulk Insert를 위한 객체 리스트 생성
            for item in ticker_data_list:
                market_code = item.get('market')
                if not market_code: continue

                try:
                    list_instance = CoinsUpbitList.objects.get(coins_code=market_code)

                    # Decimal()로 형 변환 시 None 대신 0을 사용하여 오류 방지
                    ticker_objects.append(
                        CoinsUpbitTicker(
                            coins_code=list_instance,
                            bat_time=start_time,  # 배치 시작 시간을 기준으로 일괄 저장

                            # Ticker API의 모든 필드를 모델에 매핑
                            ticker_trade_price=Decimal(item.get('trade_price', 0)),
                            ticker_opening_price=Decimal(item.get('opening_price', 0)),
                            ticker_high_price=Decimal(item.get('high_price', 0)),
                            ticker_low_price=Decimal(item.get('low_price', 0)),
                            ticker_prev_closing_price=Decimal(item.get('prev_closing_price', 0)),
                            ticker_change=item.get('change'),
                            ticker_signed_change_price=Decimal(item.get('signed_change_price', 0)),
                            ticker_signed_change_rate=Decimal(item.get('signed_change_rate', 0)),
                            ticker_trade_volume=Decimal(item.get('trade_volume', 0)),
                            ticker_acc_trade_price_24h=Decimal(item.get('acc_trade_price_24h', 0)),
                            ticker_acc_trade_volume_24h=Decimal(item.get('acc_trade_volume_24h', 0)),
                            ticker_highest_52_week_price=Decimal(item.get('highest_52_week_price', 0)),
                            ticker_highest_52_week_date=item.get('highest_52_week_date'),
                            ticker_lowest_52_week_price=Decimal(item.get('lowest_52_week_price', 0)),
                            ticker_lowest_52_week_date=item.get('lowest_52_week_date'),
                            ticker_trade_date=item.get('trade_date'),
                            ticker_trade_time=item.get('trade_time'),
                            ticker_timestamp=item.get('timestamp'),

                            # 기타 여유 필드는 None으로 둡니다.
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
            error_message = (
                f"치명적인 Ticker 데이터 저장 오류 (트랜잭션 Rollback): {e}\n\n"
                f"Traceback:\n`{traceback.format_exc()[:1000]}... (생략)`"
            )
            self.stdout.write(self.style.ERROR(error_message))
            message = f"{batch_info_header}\n\n**제목:** Ticker 저장 트랜잭션 오류\n{error_message}"
            send_notification_telegram(message, level="FATAL")

            # 치명적인 저장 오류 시에도 데이터 삭제 로직은 실행하여 DB 공간 확보를 시도
            self.delete_old_data(start_time, batch_info_header)
            return

        # 4. 오래된 데이터 삭제
        deleted_count = self.delete_old_data(start_time, batch_info_header)

        # 5. 성공 시 최종 텔레그램 알림 **(이 부분 제거)**
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        # 성공 로그는 서버 콘솔에만 남깁니다.
        success_message = (
            f'Total Request: {total_request_count} times, '
            f'Saved: {saved_count} records, '
            f'Deleted: {deleted_count} records, '
            f'Duration: {duration:.2f} seconds.'
        )
        self.stdout.write(self.style.SUCCESS(f"Ticker Batch Success: {success_message}"))

        # 텔레그램 알림을 보내지 않고 정상 종료
        return

    def delete_old_data(self, current_time, batch_info_header):
        """
        데이터 폭증을 막기 위해 10일 이전의 Ticker 데이터를 삭제합니다.
        (대규모 삭제 발생 시 WARNING 알림은 유지)
        """
        delete_threshold = current_time - timedelta(days=self.DATA_RETENTION_DAYS)
        self.stdout.write(f"Deleting data older than: {delete_threshold.strftime('%Y-%m-%d %H:%M:%S')}...")

        try:
            with transaction.atomic():
                # bat_time이 지정된 임계값보다 작은 모든 레코드를 선택하여 삭제
                deleted, rows_count = CoinsUpbitTicker.objects.filter(
                    bat_time__lt=delete_threshold
                ).delete()

            deleted_count = rows_count.get('coins_upbit_ticker', 0)
            self.stdout.write(self.style.WARNING(f"Successfully deleted {deleted_count} old Ticker records."))

            # 대규모 삭제 발생 시 경고 알림 (유지)
            if deleted_count > 10000:
                warning_message = f"대량 데이터 삭제: {deleted_count}개의 Ticker 레코드가 삭제되었습니다. (10일 보존 정책)"
                message = f"{batch_info_header}\n\n**제목:** Ticker 데이터 정리\n{warning_message}"
                send_notification_telegram(message, level="WARNING")  # WARNING 알림은 발송

            return deleted_count

        except Exception as e:
            error_message = (
                f"치명적인 오래된 Ticker 데이터 삭제 오류: {e}\n\n"
                f"Traceback:\n`{traceback.format_exc()[:1000]}... (생략)`"
            )
            self.stdout.write(self.style.ERROR(error_message))
            message = f"{batch_info_header}\n\n**제목:** Ticker 삭제 오류\n{error_message}"
            send_notification_telegram(message, level="FATAL")  # FATAL 알림은 발송
            return 0