import os
import traceback
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import FinanceDataReader as fdr
from TheaterWinBook.models_stock_usa import StocksUsList
from TheaterWinBook.utils_telegram import send_notification_telegram


class Command(BaseCommand):
    help = 'NASDAQ, NYSE, AMEX 종목 리스트를 수집하고 상폐 종목을 자동으로 비활성화합니다.'

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
        processed_symbols = []  # 이번 배치에서 확인된 티커들

        try:
            self.stdout.write(self.style.SUCCESS("🚀 미국 주식 리스트 수집 시작..."))

            # 주요 시장(NYSE, NASDAQ, AMEX) 데이터를 한 번에 가져오거나 병합
            # fdr.StockListing('S&P500') 등을 추가로 활용할 수도 있습니다.
            df = fdr.StockListing('NYSE')
            df_nasdaq = fdr.StockListing('NASDAQ')


            import pandas as pd
            df_combined = pd.concat([df, df_nasdaq]).drop_duplicates(subset=['Symbol'])

            # 2. 데이터 저장 (트랜잭션 적용)
            with transaction.atomic():
                for _, row in df_combined.iterrows():
                    symbol = row.get('Symbol')
                    if not symbol: continue

                    # update_or_create를 통해 기존 종목은 갱신하고, is_active를 True로 유지/변경
                    obj, created = StocksUsList.objects.update_or_create(
                        symbol=symbol,
                        defaults={
                            'name_en': row.get('Name', ''),
                            'industry': row.get('Industry', ''),
                            'sector': row.get('Sector', ''),
                            'market': row.get('Exchange', 'US'),
                            'is_active': True  # 현재 목록에 있으므로 무조건 활성화
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    processed_symbols.append(symbol)

                # 3. 상장 폐지/제외 종목 처리 (Deactivation)
                # DB에는 is_active=True인데, 이번 수집된 리스트(processed_symbols)에는 없는 종목들
                deactivated_count = 0
                if processed_symbols:
                    deactivated_count = StocksUsList.objects.filter(
                        is_active=True
                    ).exclude(
                        symbol__in=processed_symbols
                    ).update(
                        is_active=False
                    )

            # 4. 결과 보고
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            success_summary = (
                f"**수집 대상:** US Markets (NYSE/NASDAQ/AMEX)\n"
                f"**신규 등록:** {created_count}개\n"
                f"**정보 갱신:** {updated_count}개\n"
                f"**상폐 비활성화:** {deactivated_count}개\n"
                f"**소요 시간:** {duration:.2f}초"
            )

            message = f"{batch_info_header}\n\n**제목:** 미국 주식 리스트 동기화 완료\n{success_summary}"
            send_notification_telegram(message, level="SUCCESS", category="미국주식")
            self.stdout.write(self.style.SUCCESS(f"배치 완료: 신규 {created_count}, 비활성 {deactivated_count}"))

        except Exception as e:
            error_trace = traceback.format_exc()
            fatal_message = f"{batch_info_header}\n\n**제목:** 미국 주식 수집 치명적 오류\n`{e}`\n\n**Traceback:**\n`{error_trace}`"
            send_notification_telegram(fatal_message, level="FATAL", category="미국주식")
            self.stdout.write(self.style.ERROR(f"에러 발생: {e}"))