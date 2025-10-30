import requests
import time
import sys
import traceback
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings
# 💡 모델 경로 확인: 필요시 TheaterWinBook.models_basedb 대신 정확한 경로 사용
from TheaterWinBook.models_basedb import EcosIndicator
from datetime import datetime, timedelta
import os


# --- 텔레그램 알림 헬퍼 함수 (동일하게 유지) ---
def send_notification_telegram(message, level="INFO"):
    """
    텔레그램 봇을 통해 메시지를 발송하는 헬퍼 함수.
    """
    try:
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
        if not token or not chat_id:
            print("[CRITICAL] TELEGRAM_BOT_TOKEN 또는 CHAT_ID 설정 오류. 알림 실패.")
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
        print(f"[CRITICAL] Error sending Telegram notification for {level}: {e}")


# -------------------------------------------------------------------


class Command(BaseCommand):
    help = 'Fetches major macro economic indicators from BOK ECOS API and saves them to DB.'

    # 💡 최종 확정된 지표 목록: Cycle 유지
    INDICATORS_TO_FETCH = [
        {'stat_code': '030Y001', 'item_code': '0000001', 'name': '한국은행 기준금리', 'unit': '%', 'cycle': 'M'},
        {'stat_code': '901Y001', 'item_code': '0000001', 'name': '환율_원/달러', 'unit': 'KRW/USD', 'cycle': 'M'},
        {'stat_code': '901Y002', 'item_code': '0000001', 'name': '환율_원/엔', 'unit': 'KRW/JPY', 'cycle': 'M'},
        {'stat_code': '200Y001', 'item_code': 'A0101011', 'name': 'GDP_실질_경제성장률(전기대비)', 'unit': '%', 'cycle': 'Q'},
        {'stat_code': '600Y001', 'item_code': 'A', 'name': '광의통화(M2)_총통화', 'unit': '십억원', 'cycle': 'M'},
        {'stat_code': '500Y001', 'item_code': 'A0100000', 'name': '소비자 물가 지수(총지수)', 'unit': '2020=100', 'cycle': 'M'},
        {'stat_code': '500Y002', 'item_code': 'A0100000', 'name': '생산자 물가 지수(총지수)', 'unit': '2020=100', 'cycle': 'M'},
        {'stat_code': '800Y001', 'item_code': '01000', 'name': '기업경기실사지수(BSI)_전산업', 'unit': 'Index', 'cycle': 'M'},
        {'stat_code': '800Y002', 'item_code': 'B1', 'name': '소비자심리지수(CSI)_현재생활형편', 'unit': 'Index', 'cycle': 'M'},
    ]

    ECOS_BASE_URL = "http://ecos.bok.or.kr/api/StatisticSearch"
    RESULT_FORMAT = "json"
    LANGUAGE_CODE = "kr"
    MAX_ROWS_PER_CALL = 1000

    # 💡 10년 전 날짜를 datetime 객체로 미리 계산
    START_DT_OBJ = datetime.now() - timedelta(days=365 * 10)
    END_DT_OBJ = datetime.now()

    def handle(self, *args, **options):
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

        self.stdout.write(self.style.SUCCESS('Starting ECOS Macro Indicator data batch...'))

        API_KEY = getattr(settings, 'ECOS_API_KEY', None)
        if not API_KEY:
            warning_msg = "[FATAL] ECOS_API_KEY가 설정되지 않았습니다. .env 및 settings.py 확인 후 배치 중단."
            self.stdout.write(self.style.ERROR(warning_msg))
            send_notification_telegram(f"**배치 파일:** `{command_file_name}`\n\n{warning_msg}", level="FATAL")
            return

        failed_indicators = []
        total_indicators = len(self.INDICATORS_TO_FETCH)
        processed_indicators = 0

        batch_info_header = (
            f"**배치 파일:** `{command_file_name}`\n"
            f"**배치 시작 시간:** `{start_time_str}`\n"
            f"---"
        )

        # 1. 메인 루프: 지표별 반복
        for indicator in self.INDICATORS_TO_FETCH:
            stat_code = indicator['stat_code']
            item_code = indicator['item_code']
            indicator_name = indicator['name']
            indicator_unit = indicator['unit']
            cycle = indicator['cycle']

            self.stdout.write(f"\n--- 📈 Fetching: {indicator_name} ({stat_code}, Cycle: {cycle}) ---")

            # 💡💡💡 주기(Cycle)에 맞춰 요청 날짜 형식(START_DATE/END_DATE) 동적 설정 💡💡💡
            # ECOS API 요구사항: D=YYYYMMDD, M=YYYYMM, Q=YYYYQ, A=YYYY
            if cycle == 'D':
                start_date = self.START_DT_OBJ.strftime('%Y%m%d')
                end_date = self.END_DT_OBJ.strftime('%Y%m%d')
            elif cycle == 'M':
                start_date = self.START_DT_OBJ.strftime('%Y%m')
                # 월별 데이터는 해당 월의 마지막 날짜를 요구하지 않고 YYYYMM 형식만 요구
                end_date = self.END_DT_OBJ.strftime('%Y%m')
            elif cycle == 'Q':
                start_date = self.START_DT_OBJ.strftime(
                    '%Y') + f"{(self.START_DT_OBJ.month - 1) // 3 + 1}Q"  # YYYYQ 포맷 생성
                end_date = self.END_DT_OBJ.strftime('%Y') + f"{(self.END_DT_OBJ.month - 1) // 3 + 1}Q"
            elif cycle == 'A':
                start_date = self.START_DT_OBJ.strftime('%Y')
                end_date = self.END_DT_OBJ.strftime('%Y')
            else:
                self.stdout.write(
                    self.style.ERROR(f"  [FATAL] Unknown cycle '{cycle}' for {indicator_name}. Skipping."))
                continue

            self.stdout.write(f"  [Date Format] Start: {start_date}, End: {end_date}")

            start_index = 1
            is_fetching_done = False
            call_count = 0

            while not is_fetching_done:
                try:
                    call_count += 1

                    end_index = start_index + self.MAX_ROWS_PER_CALL - 1

                    url = (
                        f"{self.ECOS_BASE_URL}/{API_KEY}/{self.RESULT_FORMAT}/"
                        f"{self.LANGUAGE_CODE}/"
                        f"{start_index}/{end_index}/"
                        f"{stat_code}/{cycle}/{start_date}/{end_date}/{item_code}"  # 💡 동적으로 변경된 start_date/end_date 사용
                    )

                    self.stdout.write(f"  [API Call {call_count}] URL (Indexes): {start_index} to {end_index}")

                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    # 1-2. 데이터 파싱 및 에러 체크
                    stat_data_root = data.get('StatisticSearch')

                    if not stat_data_root and data.get('RESULT'):
                        error_result = data.get('RESULT')
                        error_msg = f"Code: {error_result.get('CODE')}, Message: {error_result.get('MESSAGE')}"
                        raise requests.exceptions.RequestException(f"ECOS API Error (Call {call_count}): {error_msg}")

                    elif not stat_data_root:
                        raise requests.exceptions.RequestException(
                            f"ECOS API Error (Call {call_count}): Unexpected API response format.")

                    data_list = stat_data_root.get('row', [])
                    total_count = stat_data_root.get('list_total_count', 0)

                    if not data_list:
                        self.stdout.write(
                            f"  [API Call {call_count}] No more data or finished fetching. (Total: {total_count})")
                        is_fetching_done = True
                        break

                    # 💡 DB 저장 활성화 (1-3. DB 저장)
                    with transaction.atomic():
                        for row in data_list:
                            try:
                                time_period = row.get('TIME_PERIOD')
                                data_value_str = row.get('DATA_VALUE')

                                # 💡 DB 저장용 날짜 포맷팅 (기준: 해당 기간의 첫째 날)
                                if len(time_period) == 8:  # YYYYMMDD
                                    data_date = datetime.strptime(time_period, '%Y%m%d').date()
                                elif len(time_period) == 6:  # YYYYMM
                                    data_date = datetime.strptime(time_period + '01', '%Y%m%d').date()
                                elif len(time_period) == 5 and 'Q' in time_period:  # YYYYQ
                                    year, quarter = int(time_period[:4]), int(time_period[4])
                                    month = [1, 4, 7, 10][quarter - 1]
                                    data_date = datetime(year, month, 1).date()
                                elif len(time_period) == 4:  # YYYY (연간)
                                    data_date = datetime.strptime(time_period + '0101', '%Y%m%d').date()
                                else:
                                    self.stdout.write(self.style.WARNING(
                                        f"Unknown date format for {indicator_name}: {time_period}. Skipping."))
                                    continue

                                data_value = float(data_value_str) if data_value_str else None

                                EcosIndicator.objects.update_or_create(
                                    stat_code=stat_code,
                                    item_code=item_code,
                                    data_date=data_date,
                                    defaults={
                                        'bat_time': timezone.now(),
                                        'indicator_name': indicator_name,
                                        'indicator_unit': indicator_unit,
                                        'data_value': data_value,
                                    }
                                )
                            except Exception as db_e:
                                error_msg = f"DB Error: {str(db_e)}"
                                failed_indicators.append({
                                    'indicator': indicator_name, 'date': time_period or 'N/A',
                                    'type': 'DB_ERROR', 'error': error_msg
                                })
                                self.stdout.write(
                                    self.style.ERROR(f"DB Error for {indicator_name} on {time_period}: {db_e}"))
                                pass

                    # 1-4. 다음 페이지 설정 및 종료 조건 확인
                    start_index = end_index + 1

                    if start_index > total_count:
                        is_fetching_done = True

                    self.stdout.write(f"  [API Call {call_count}] Batch saved. Next index: {start_index}/{total_count}")
                    time.sleep(0.5)

                except requests.exceptions.RequestException as e:
                    error_msg = f"API Request Error: {str(e)}"
                    failed_indicators.append({
                        'indicator': indicator_name, 'date': 'N/A', 'type': 'API_ERROR', 'error': error_msg
                    })
                    self.stdout.write(
                        self.style.ERROR(f"  [ERROR] API Request Error for {indicator_name}: {e}. Skipping."))
                    time.sleep(1)
                    break

                except Exception as e:
                    error_msg = f"Unexpected Error: {e}\n{traceback.format_exc()[:200]}..."
                    failed_indicators.append({
                        'indicator': indicator_name, 'date': 'N/A', 'type': 'UNEXPECTED_ERROR', 'error': error_msg
                    })
                    self.stdout.write(self.style.ERROR(f"  [FATAL] An unexpected error occurred: {e}. Skipping."))
                    break

            processed_indicators += 1

        # 2. 최종 완료 및 텔레그램 알림
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        summary_message = (
            f'**총 대상 지표:** {total_indicators}\n'
            f'**총 처리 완료:** {processed_indicators}\n'
            f'**총 오류 건수:** {len(failed_indicators)}건\n'
            f'**소요 시간:** {duration:.2f} 초'
        )

        level = "SUCCESS"
        if failed_indicators:
            level = "ERROR"
            error_summary_list = [
                f"[{fail['type'].replace('_', ' ')}] `{fail['indicator']}` ({fail['date']}): {fail['error'][:150]}..."
                for fail in failed_indicators[:15]]
            error_summary_text = "\n" + "\n".join(error_summary_list)

            final_message = (
                f"{batch_info_header}\n\n"
                f"**제목:** ECOS 지표 배치 완료 (오류 발생)\n"
                f"{summary_message}\n"
                f"\n**--- 데이터 저장 실패 상세 ---**{error_summary_text}"
            )
        else:
            final_message = (
                f"{batch_info_header}\n\n"
                f"**제목:** ECOS 지표 배치 완료 (성공)\n"
                f"{summary_message}"
            )

        send_notification_telegram(final_message, level=level)
        self.stdout.write(self.style.SUCCESS(f'\n--- ECOS data collection completed in {duration:.2f} seconds. ---'))