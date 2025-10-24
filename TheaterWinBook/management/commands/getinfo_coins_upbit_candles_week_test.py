import requests
import time
import sys
import traceback
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from TheaterWinBook.models_coins import CoinsUpbitList, CoinsUpbitCandle
from datetime import datetime, timedelta
import os


# --- 텔레그램 알림 헬퍼 함수 (이전에 정상 작동 확인된 코드) ---
def send_notification_telegram(message, level="INFO"):
    """
    텔레그램 봇을 통해 메시지를 발송하는 헬퍼 함수.
    """
    try:
        # settings 접근 시 오류 처리 강화
        try:
            token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID
        except AttributeError:
            print("[CRITICAL] TELEGRAM_BOT_TOKEN 또는 CHAT_ID 설정 오류 (settings.py 누락). 알림 실패.")
            return

        API_URL = f"https://api.telegram.org/bot{token}/sendMessage"

        if len(message) > 4000:
            message = message[:3900] + "\n\n... [메시지 길이 제한으로 생략됨] ..."

        tag = f"🚨 [치명적 오류] 🚨\n" if level == "FATAL" else \
            f"❌ [데이터 오류] ❌\n" if level == "ERROR" else \
                f"⚠️ [경고] ⚠️\n" if level == "WARNING" else \
                    f"✅ [배치 완료] ✅\n"

        full_message = tag + message

        params = {'chat_id': chat_id, 'text': full_message, 'parse_mode': 'Markdown'}
        requests.post(API_URL, data=params, timeout=5).raise_for_status()

    except Exception as e:
        # API 호출 실패, 네트워크 오류 등
        print(f"[CRITICAL] Error sending Telegram notification for {level}: {e}")
        # 이 함수가 실패하더라도 메인 배치는 계속 진행되어야 합니다.


# -------------------------------------------------------------------


class Command(BaseCommand):
    help = 'Fetches Upbit daily candle data for all active coins for the last 7 days (Weekly Batch Update).'

    def handle(self, *args, **options):
        # 배치 정보 초기화
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

        self.stdout.write(self.style.SUCCESS('Starting Upbit 7-day daily candle data update batch...'))

        API_URL = "https://api.upbit.com/v1/candles/days"

        # 💡 [핵심]: is_active=True인 코인만 필터링하여 가져옵니다.
        coins_list = CoinsUpbitList.objects.filter(is_active=True)

        failed_candles = []
        total_active_coins = coins_list.count() # 필터링된 코인 개수
        processed_coins = 0

        batch_info_header = (
            f"**배치 파일:** `{command_file_name}`\n"
            f"**배치 시작 시간:** `{start_time_str}`\n"
            f"---"
        )

        if not coins_list.exists():
            warning_msg = "CoinsUpbitList에 현재 활성 상태(is_active=True)인 코인이 없습니다. 리스트 배치를 확인하세요."
            self.stdout.write(self.style.WARNING(warning_msg))
            send_notification_telegram(f"{batch_info_header}\n\n{warning_msg}", level="WARNING")
            return

        DAYS_TO_FETCH = 7

        # 1. 메인 루프: 에러 발생 시 중단 없이 다음 코인으로 진행
        for coin in coins_list:
            market_code = coin.coins_code
            self.stdout.write(f"Fetching last {DAYS_TO_FETCH} days data for {market_code}...")

            is_all_candles_ok = True

            try:
                # 1-1. API 요청
                params = {
                    "market": market_code,
                    "count": DAYS_TO_FETCH
                }

                response = requests.get(API_URL, params=params)
                response.raise_for_status()
                data = response.json()

                processed_coins += 1

                if not data:
                    self.stdout.write(f"No candle data found for {market_code}. Skipping to next coin.")
                    continue

                # 1-2. DB 저장 (개별 캔들 처리)
                for candle in data:
                    candle_date_time_kst = candle.get('candle_date_time_kst')

                    try:
                        CoinsUpbitCandle.objects.update_or_create(
                            coins_code=coin,
                            coin_candle_datetime_kst=candle_date_time_kst,
                            defaults={
                                'bat_time': timezone.now(),
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

                    except Exception as db_e:
                        # 💡 DB 저장 오류 발생 시 실패 리스트에 추가
                        error_msg = f"DB Error: {str(db_e)}"
                        failed_candles.append({
                            'coin': market_code,
                            'date': candle_date_time_kst or 'N/A',
                            'type': 'DB_ERROR',
                            'error': error_msg
                        })
                        self.stdout.write(
                            self.style.ERROR(f"DB Error for {market_code} on {candle_date_time_kst}: {db_e}"))
                        is_all_candles_ok = False # 이 코인의 전체 캔들 저장이 완벽하지 않음
                        pass

                # 💡 last_candle_batch_time 업데이트 로직 제거 완료.

                # 3. 성공 시 메시지 및 지연
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully processed {len(data)} candles for {market_code} (All candles OK: {is_all_candles_ok})."))
                time.sleep(0.2)

            except requests.exceptions.RequestException as e:
                # 💡 API 요청 오류 발생 시 실패 리스트에 추가하고 다음 코인으로 진행
                error_msg = f"API Request Error: {str(e)}"
                failed_candles.append({
                    'coin': market_code,
                    'date': 'N/A',
                    'type': 'API_ERROR',
                    'error': error_msg
                })
                self.stdout.write(self.style.ERROR(f"API Request Error for {market_code}: {e}. Skipping..."))
                time.sleep(1)
                continue

            except Exception as e:
                # 💡 예상치 못한 오류 발생 시 실패 리스트에 추가하고 다음 코인으로 진행
                error_msg = f"Unexpected Error: {e}\n{traceback.format_exc()[:200]}..."
                failed_candles.append({
                    'coin': market_code,
                    'date': 'N/A',
                    'type': 'UNEXPECTED_ERROR',
                    'error': error_msg
                })
                self.stdout.write(
                    self.style.ERROR(f"An unexpected error occurred during processing {market_code}: {e}. Skipping..."))
                continue

        # 2. 최종 완료 및 텔레그램 알림
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        summary_message = (
            f'**총 활성 코인:** {total_active_coins}\n'
            f'**총 처리 시도:** {processed_coins}\n'
            f'**총 오류 건수:** {len(failed_candles)}건\n'
            f'**소요 시간:** {duration:.2f} 초'
        )

        if failed_candles:
            error_summary_list = []
            for i, fail in enumerate(failed_candles[:15]):
                error_summary_list.append(
                    f"[{fail['type'].replace('_', ' ')}] `{fail['coin']}` ({fail['date']}): {fail['error'][:200]}..."
                )

            error_summary_text = "\n" + "\n".join(error_summary_list)
            if len(failed_candles) > 15:
                error_summary_text += f"\n... 외 {len(failed_candles) - 15}건 생략"

            final_message = (
                f"{batch_info_header}\n\n"
                f"**제목:** Upbit 캔들 배치 완료 (오류 발생)\n"
                f"{summary_message}\n"
                f"\n**--- 캔들 저장 실패 상세 ---**{error_summary_text}"
            )
            send_notification_telegram(final_message, level="ERROR")
        else:
            final_message = (
                f"{batch_info_header}\n\n"
                f"**제목:** Upbit 1주일 캔들 배치 완료 (성공)\n"
                f"{summary_message}"
            )
            send_notification_telegram(final_message, level="SUCCESS")

        self.stdout.write(self.style.SUCCESS('Upbit 7-day daily candle batch update completed.'))