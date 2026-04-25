import os
import traceback
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import FinanceDataReader as fdr
from TheaterWinBook.models_stock_korea import StocksKrList
from TheaterWinBook.utils_telegram import send_notification_telegram


class Command(BaseCommand):
    help = 'KOSPI, KOSDAQ, ETF 리스트를 개별적으로 수집하여 안정성을 높이고 상폐 종목을 비활성화합니다.'

    def handle(self, *args, **options):
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()

        batch_info_header = (
            f"**배치 파일:** `{command_file_name}`\n"
            f"**배치 시작 시간:** `{start_time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"---"
        )

        created_count = 0
        updated_count = 0
        processed_codes = []

        try:
            self.stdout.write(self.style.SUCCESS("🚀 한국 주식 리스트 수집 시작 (개별 시장 접근)..."))

            # [변경] 통합 KRX 대신 개별 시장 소스를 순차적으로 호출하여 리스크 분산
            # FDR 버전별로 구현 방식이 다를 수 있어 가장 기본 소스들로 구성
            market_targets = [
                {'name': 'KOSPI', 'label': 'KOSPI'},
                {'name': 'KOSDAQ', 'label': 'KOSDAQ'},
                {'name': 'ETF/KR', 'label': 'ETF'}
            ]

            dfs = []
            for target in market_targets:
                try:
                    self.stdout.write(f"  - {target['label']} 수집 중...")
                    df_target = fdr.StockListing(target['name'])
                    if not df_target.empty:
                        print("df_target is not empty")
                        # 시장 구분 컬럼 강제 삽입
                        df_target['Market_Tag'] = target['label']
                        dfs.append(df_target)
                except Exception as target_e:
                    self.stdout.write(self.style.WARNING(f"    ⚠️ {target['label']} 실패: {target_e}"))

            if not dfs:
                raise Exception("모든 시장 소스 수집 실패")

            df_combined = pd.concat(dfs).drop_duplicates(subset=['Symbol', 'Code'], keep='first')

            # 2. 데이터 저장 (트랜잭션 적용)
            with transaction.atomic():
                for _, row in df_combined.iterrows():
                    code = row.get('Code') or row.get('Symbol')
                    if not code: continue

                    code = str(code).zfill(6)

                    # ETF 여부 판단 로직 고도화
                    market = row.get('Market_Tag')
                    if market == 'ETF' or 'ETF' in str(row.get('Name', '')):
                        market = 'ETF'

                    industry = row.get('Sector') or row.get('Industry', '')

                    obj, created = StocksKrList.objects.update_or_create(
                        stock_code=code,
                        defaults={
                            'stock_name': row.get('Name', 'Unknown'),
                            'market_type': market,
                            'industry': industry,
                            'is_active': True
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                    processed_codes.append(code)

                # 3. 상장 폐지/제외 종목 처리
                deactivated_count = 0
                if processed_codes:
                    deactivated_count = StocksKrList.objects.filter(
                        is_active=True
                    ).exclude(
                        stock_code__in=processed_codes
                    ).update(is_active=False)

            # 4. 결과 보고
            duration = (timezone.now() - start_time).total_seconds()
            success_summary = (
                f"**수집 성공:** {created_count + updated_count}건\n"
                f"- 신규 등록: {created_count}개\n"
                f"- 상폐 비활성화: {deactivated_count}개\n"
                f"**소요 시간:** {duration:.2f}초"
            )

            message = f"{batch_info_header}\n\n**제목:** 한국 주식 리스트 동기화 완료\n{success_summary}"
            send_notification_telegram(message, level="SUCCESS", category="한국주식")
            self.stdout.write(self.style.SUCCESS("✅ 배치 성공"))

        except Exception as e:
            error_trace = traceback.format_exc()
            fatal_message = f"{batch_info_header}\n\n**제목:** 한국 주식 수집 치명적 오류\n`{e}`"
            send_notification_telegram(fatal_message, level="FATAL", category="한국주식")
            self.stdout.write(self.style.ERROR(f"에러 발생: {e}"))