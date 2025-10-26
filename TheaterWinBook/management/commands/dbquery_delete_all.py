# TheaterWinBook/management/commands/dbquery_delete_all.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
import os
import shutil
import glob

# 모델 임포트 경로는 실제 프로젝트에 맞게 확인해주세요.
from TheaterWinBook.models_coins import CoinsUpbitTicker
from django.apps import apps  # 앱 설정을 가져오기 위해 필요


class Command(BaseCommand):
    help = 'Deletes all records from CoinsUpbitTicker and guides on migration file cleanup to resolve schema conflicts.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🚨 [경고] Upbit Ticker 데이터베이스 초기화 시작'))

        # 1. Ticker 데이터 삭제
        try:
            with transaction.atomic():
                deleted_count, details = CoinsUpbitTicker.objects.all().delete()

            total_deleted = details.get('coins_upbit_ticker', 0)
            self.stdout.write(
                self.style.SUCCESS(f'✅ CoinsUpbitTicker 테이블에서 총 {total_deleted}개 레코드를 삭제했습니다.')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ticker 데이터 삭제 중 치명적인 오류 발생: {e}')
            )
            return

        # 2. 마이그레이션 파일 정리 안내
        app_name = 'TheaterWinBook'  # 🚨 실제 앱 이름으로 수정해야 합니다.
        app_config = apps.get_app_config(app_name)
        migrations_dir = os.path.join(app_config.path, 'migrations')

        # 최신 마이그레이션 파일 목록 확인 (최대 5개)
        migration_files = sorted(
            glob.glob(os.path.join(migrations_dir, '[0-9][0-9][0-9][0-9]_*.py'))
        )[-5:]

        self.stdout.write(self.style.WARNING('\n----------------------------------------'))
        self.stdout.write(self.style.WARNING('⚠️ 다음 단계: 마이그레이션 파일 수동 정리 및 재생성'))
        self.stdout.write(self.style.WARNING('----------------------------------------'))
        self.stdout.write(
            "이전 오류는 Ticker 모델의 PK 변경으로 인한 것입니다. DB 레코드 삭제 외에, Django의 기록도 지워야 합니다."
        )
        self.stdout.write(
            f"**1. `TheaterWinBook` 앱의 {migrations_dir} 폴더에서 " + self.style.ERROR(
                'CoinsUpbitTicker') + "와 관련된 최근 마이그레이션 파일을 삭제하십시오. (혹은 0001_initial.py를 제외한 모든 파일)"
        )

        if migration_files:
            self.stdout.write("   - 확인해야 할 최근 마이그레이션 파일:")
            for f in migration_files:
                self.stdout.write(f"     -> {os.path.basename(f)}")

        self.stdout.write("\n**2. 모델을 원하는 OneToOneField 구조로 확정하고 다음 명령을 실행하십시오:**")
        self.stdout.write(self.style.SUCCESS('   $ python manage.py makemigrations TheaterWinBook'))
        self.stdout.write(self.style.SUCCESS('   $ python manage.py migrate'))

        self.stdout.write('\n초기화가 완료되었습니다. 새 Ticker 모델로 마이그레이션 파일을 생성해 주십시오.')