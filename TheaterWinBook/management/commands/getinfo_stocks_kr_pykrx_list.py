import os
import sys
import traceback
import requests
from datetime import date
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db import transaction
import FinanceDataReader as fdr
from TheaterWinBook.models_stock_korea import StocksKrList


# 텔레그램 알림 함수 (공통 모듈화 권장)
def send_notification_telegram(message, level="INFO"):
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
    except AttributeError:
        print("[CRITICAL] Telegram settings missing.")
        return

    API_URL = f"https://api.telegram.org/bot{token}/sendMessage"
    tag = {
        "FATAL": "🚨 [주식-치명적 오류] 🚨\n",
        "ERROR": "❌ [주식-데이터 오류] ❌\n",
        "SUCCESS": "✅ [주식-배치 완료] ✅\n",
        "INFO": "ℹ️ [주식-알림] ℹ️\n"
    }.get(level, "")

    full_message = tag + message
    if len(full_message) > 4000:
        full_message = full_message[:3900] + "\n..."

    try:
        requests.post(API_URL, data={'chat_id': chat_id, 'text': full_message, 'parse_mode': 'Markdown'}, timeout=5)
    except Exception as e:
        print(f"Telegram failed: {e}")


class Command(BaseCommand):
    help = 'KOSPI, KOSDAQ 및 ETF 리스트를 수집하고 텔레그램으로 보고합니다.'

    def handle(self, *args, **options):
        # 1. 초기 설정
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

        batch_info_header = (
            f"**배치 파일:** `{command_file_name}`\n"
            f"**배치 시작 시간:** `{start_time_str}`\n"
            f"---"
        )

        processed_codes = []
        failed_targets = []
        created_count = 0
        updated_count = 0

        targets = [
            {'name': 'KRX', 'is_etf': False},
            {'name': 'ETF/KR', 'is_etf': True}
        ]

        self.stdout.write(self.style.SUCCESS(f"🚀 주식 리스트 수집 시작: {start_time_str}"))

        try:
            for target in targets:
                self.stdout.write(f"수집 중: {target['name']}...")
                try:
                    df = fdr.StockListing(target['name'])

                    # 데이터프레임 표준화
                    df = df.rename(columns={'Symbol': 'Code', 'Sector': 'Industry'})
                    if 'Code' not in df.columns:
                        df = df.reset_index().rename(columns={'index': 'Code', 'Symbol': 'Code'})

                except Exception as e:
                    error_msg = f"{target['name']} API 수집 실패: {e}"
                    self.stdout.write(self.style.ERROR(error_msg))
                    failed_targets.append(target['name'])
                    continue

                # 개별 종목 처리 (원자성 확보를 위해 트랜잭션 사용 고려 가능)
                for _, row in df.iterrows():
                    code = row.get('Code')
                    if not code: continue

                    market = row.get('Market', 'ETF')
                    if not target['is_etf'] and market not in ['KOSPI', 'KOSDAQ']:
                        continue

                    stock_name = row.get('Name', 'Unknown')
                    industry = 'ETF' if target['is_etf'] else row.get('Industry', row.get('Sector', ''))

                    try:
                        obj, created = StocksKrList.objects.update_or_create(
                            stock_code=code,
                            defaults={
                                'stock_name': stock_name,
                                'market_type': market,
                                'industry': industry,
                                'is_active': True,
                            }
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                        processed_codes.append(code)
                    except Exception as db_e:
                        self.stdout.write(self.style.ERROR(f"DB 저장 오류 ({code}): {db_e}"))

            # 2. 상장 폐지 및 제외 종목 비활성화
            deactivated_count = 0
            if processed_codes:
                deactivated_count = StocksKrList.objects.filter(is_active=True).exclude(
                    stock_code__in=processed_codes
                ).update(is_active=False)

            # 3. 최종 결과 보고
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            success_summary = (
                f"**수집 대상:** KRX, ETF/KR\n"
                f"**신규 등록:** {created_count}개\n"
                f"**정보 갱신:** {updated_count}개\n"
                f"**상폐/제외:** {deactivated_count}개 비활성화\n"
                f"**소요 시간:** {duration:.2f}초\n"
                f"**API 실패:** {', '.join(failed_targets) if failed_targets else '없음'}"
            )

            self.stdout.write(self.style.SUCCESS(f"완료: {success_summary}"))

            # 텔레그램 전송
            message = f"{batch_info_header}\n\n**제목:** 한국 주식 리스트 동기화 완료\n{success_summary}"
            send_notification_telegram(message, level="SUCCESS")

        except Exception as e:
            error_trace = traceback.format_exc()
            self.stdout.write(self.style.ERROR(f"치명적 오류: {e}"))
            fatal_message = f"{batch_info_header}\n\n**제목:** 주식 리스트 수집 치명적 오류\n`{e}`\n\n**Traceback:**\n`{error_trace}`"
            send_notification_telegram(fatal_message, level="FATAL")