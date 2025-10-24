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
    # 💡 HELP 메시지 변경
    help = 'Fetches Upbit daily candle data for all active coins for the last 3 years (Historical Data Batch).'

    def handle(self, *args, **options):
        # 배치 정보 초기화
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

        # 💡 로그 메시지 변경
        self.stdout.write(self.style.SUCCESS('Starting Upbit 3-year daily candle data historical batch...'))

        API_URL = "https://api.upbit.com/v1/candles/days"

        # is_active=True인 코인만 필터링하여 가져옵니다.
        coins_list = CoinsUpbitList.objects.filter(is_active=True)

        failed_candles = []
        total_active_coins = coins_list.count()
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

        # 💡 API 당 최대 요청 건수
        COUNT_PER_CALL = 200
        # 💡 3년치 (약 1095일)
        DAYS_FOR_HISTORY = 1095
        # 💡 필요한 API 호출 횟수 (최대)
        MAX_CALLS_PER_COIN = (DAYS_FOR_HISTORY + COUNT_PER_CALL - 1) // COUNT_PER_CALL

        # 1. 메인 루프: 에러 발생 시 중단 없이 다음 코인으로 진행
        for coin in coins_list:
            market_code = coin.coins_code
            self.stdout.write(f"Fetching {DAYS_FOR_HISTORY} days data for {market_code}...")

            is_all_candles_ok = True

            # 💡 [핵심] 3년치 데이터를 가져오기 위한 시작 시점 설정 (현재 시간)
            # API는 'to' 시점까지의 데이터를 반환하므로, 현재 시간을 기준으로 시작합니다.
            current_to_time = datetime.now()
            call_count = 0

            try:
                while call_count < MAX_CALLS_PER_COIN:  # 💡 횟수 제한 루프

                    # 1-1. API 요청
                    params = {
                        "market": market_code,
                        "count": COUNT_PER_CALL,
                        # 'to' 파라미터는 ISO 8601 포맷 (YYYY-MM-DDThh:mm:ss) 사용
                        "to": current_to_time.strftime("%Y-%m-%dT%H:%M:%S")
                    }

                    response = requests.get(API_URL, params=params)
                    response.raise_for_status()
                    data = response.json()

                    call_count += 1

                    if not data:
                        self.stdout.write(
                            f"No more historical data found for {market_code} (Call {call_count}). Stopping.")
                        break  # 데이터가 없으면 루프 종료

                    # 1-2. DB 저장 (개별 캔들 처리)
                    with transaction.atomic():  # API 응답 하나의 캔들을 트랜잭션으로 묶어 DB 쓰기 안정화
                        for candle in data:
                            candle_date_time_kst = candle.get('candle_date_time_kst')

                            try:
                                CoinsUpbitCandle.objects.update_or_create(
                                    coins_code=coin,
                                    coin_candle_datetime_kst=candle_date_time_kst,
                                    defaults={
                                        'bat_time': timezone.now(),
                                        'coin_candle_datetime_utc': candle.get('candle_date_time_time_utc'),
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
                                # DB 저장 오류 발생 시 실패 리스트에 추가
                                error_msg = f"DB Error: {str(db_e)}"
                                failed_candles.append({
                                    'coin': market_code,
                                    'date': candle_date_time_kst or 'N/A',
                                    'type': 'DB_ERROR',
                                    'error': error_msg
                                })
                                self.stdout.write(
                                    self.style.ERROR(f"DB Error for {market_code} on {candle_date_time_kst}: {db_e}"))
                                is_all_candles_ok = False
                                pass

                    # 💡 다음 API 호출을 위해 가장 오래된 데이터의 시간으로 current_to_time 업데이트
                    # Upbit API는 응답 리스트의 마지막 요소가 가장 오래된 데이터입니다.
                    oldest_candle_time_str = data[-1]['candle_date_time_kst']
                    # 'T'를 포함한 문자열을 datetime 객체로 변환
                    current_to_time = datetime.strptime(oldest_candle_time_str, '%Y-%m-%dT%H:%M:%S') - timedelta(
                        seconds=1)

                    self.stdout.write(
                        f"Batch {call_count}/{MAX_CALLS_PER_COIN} processed for {market_code}. Next 'to' time: {current_to_time.strftime('%Y-%m-%d %H:%M:%S')}")

                    # 3. Rate Limit 지연
                    time.sleep(0.2)

                # 코인별 최종 처리 완료
                processed_coins += 1  # 코인별 처리 완료 카운트 (API 호출 횟수 아님)

            except requests.exceptions.RequestException as e:
                error_msg = f"API Request Error: {str(e)}"
                failed_candles.append({
                    'coin': market_code,
                    'date': 'N/A',
                    'type': 'API_ERROR',
                    'error': error_msg
                })
                self.stdout.write(self.style.ERROR(f"API Request Error for {market_code}: {e}. Skipping to next coin."))
                time.sleep(1)
                continue

            except Exception as e:
                error_msg = f"Unexpected Error: {e}\n{traceback.format_exc()[:200]}..."
                failed_candles.append({
                    'coin': market_code,
                    'date': 'N/A',
                    'type': 'UNEXPECTED_ERROR',
                    'error': error_msg
                })
                self.stdout.write(
                    self.style.ERROR(
                        f"An unexpected error occurred during processing {market_code}: {e}. Skipping to next coin."))
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
                f"**제목:** Upbit 3년 캔들 배치 완료 (오류 발생)\n"  # 💡 제목 변경
                f"{summary_message}\n"
                f"\n**--- 캔들 저장 실패 상세 ---**{error_summary_text}"
            )
            send_notification_telegram(final_message, level="ERROR")
        else:
            final_message = (
                f"{batch_info_header}\n\n"
                f"**제목:** Upbit 3년 캔들 배치 완료 (성공)\n"  # 💡 제목 변경
                f"{summary_message}"
            )
            send_notification_telegram(final_message, level="SUCCESS")

        self.stdout.write(self.style.SUCCESS('Upbit 3-year daily candle data collection completed.'))