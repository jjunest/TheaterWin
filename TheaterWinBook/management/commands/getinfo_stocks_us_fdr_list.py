import os
import traceback
from django.core.management.base import BaseCommand
from django.utils import timezone
import FinanceDataReader as fdr
from TheaterWinBook.models_stock_usa import StocksUsList, StocksUsCandle, StocksUsTicker
from TheaterWinBook.utils_telegram import send_notification_telegram  # 공통 모듈 임포트


class Command(BaseCommand):
    help = 'NASDAQ, NYSE, AMEX 종목 리스트를 수집하고 보고합니다.'

    def handle(self, *args, **options):
        # 1. 초기화 및 시작 기록
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()

        batch_info_header = (
            f"**배치 파일:** `{command_file_name}`\n"
            f"**배치 시작 시간:** `{start_time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"---"
        )

        created_count = 0
        updated_count = 0
        processed_symbols = []

        try:
            self.stdout.write(self.style.SUCCESS("🚀 미국 주식 리스트 수집 시작..."))

            # fdr.StockListing('NYSE') 등은 NASDAQ, AMEX를 포함하는 경우가 많으나
            # 확실하게 하기 위해 주요 거래소를 지정하거나 통합 리스트를 가져옵니다.
            df = fdr.StockListing('NYSE')  # 혹은 'NASDAQ'

            for _, row in df.iterrows():
                symbol = row.get('Symbol')
                if not symbol: continue

                obj, created = StocksUsList.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'name_en': row.get('Name', ''),
                        'industry': row.get('Industry', ''),
                        'sector': row.get('Sector', ''),
                        'market': row.get('Exchange', 'US'),
                        'is_active': True
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1
                processed_symbols.append(symbol)

            # 상장 폐지 종목 처리
            deactivated_count = 0
            if processed_symbols:
                deactivated_count = StocksUsList.objects.filter(is_active=True).exclude(
                    symbol__in=processed_symbols
                ).update(is_active=False)

            # 2. 성공 보고서 작성
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            success_summary = (
                f"**수집 대상:** US Markets (NYSE/NASDAQ)\n"
                f"**신규 등록:** {created_count}개\n"
                f"**정보 갱신:** {updated_count}개\n"
                f"**상폐/제외:** {deactivated_count}개 비활성화\n"
                f"**소요 시간:** {duration:.2f}초"
            )

            message = f"{batch_info_header}\n\n**제목:** 미국 주식 리스트 동기화 완료\n{success_summary}"
            send_notification_telegram(message, level="SUCCESS", category="미국주식")
            self.stdout.write(self.style.SUCCESS("배치 완료 및 텔레그램 전송 성공"))

        except Exception as e:
            error_trace = traceback.format_exc()
            fatal_message = f"{batch_info_header}\n\n**제목:** 미국 주식 수집 치명적 오류\n`{e}`\n\n**Traceback:**\n`{error_trace}`"
            send_notification_telegram(fatal_message, level="FATAL", category="미국주식")
            self.stdout.write(self.style.ERROR(f"에러 발생: {e}"))