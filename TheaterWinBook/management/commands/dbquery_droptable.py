# TheaterWinBook/management/commands/drop_upbit_ticker_table.py

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
from django.db.utils import ProgrammingError


class Command(BaseCommand):
    help = 'WARNING: Permanently deletes the coins_upbit_ticker database table.'

    # 명령어 실행 시 사용자에게 확인 요청 (필수)
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skips the confirmation prompt for execution.'
        )

    def handle(self, *args, **options):
        table_name = 'coins_upbit_ticker'

        self.stdout.write(self.style.ERROR(f'🚨 [위험] 데이터베이스 테이블 삭제 경고'))
        self.stdout.write(f'이 작업은 "{table_name}" 테이블과 모든 데이터를 영구적으로 삭제합니다.')

        if not options['force']:
            confirm = input(
                f'정말 "{table_name}" 테이블을 삭제하시겠습니까? (yes/no): '
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('테이블 삭제를 취소했습니다.'))
                return

        # Django의 DB 연결을 사용하여 SQL 실행
        try:
            with connection.cursor() as cursor:
                # 데이터베이스 종류에 따라 IF EXISTS 구문 사용 권장 (테이블이 없을 때 오류 방지)
                if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    # PostgreSQL
                    sql = f"DROP TABLE {table_name} CASCADE;"
                else:
                    # SQLite, MySQL 등 (IF EXISTS는 대부분 지원)
                    sql = f"DROP TABLE IF EXISTS {table_name};"

                self.stdout.write(f"Executing SQL: {sql}")
                cursor.execute(sql)

            self.stdout.write(
                self.style.SUCCESS(f'✅ 테이블 "{table_name}"이 데이터베이스에서 영구적으로 삭제되었습니다.')
            )

        except ProgrammingError as e:
            # 테이블이 이미 존재하지 않을 경우 등 SQL 실행 오류 처리
            self.stdout.write(self.style.WARNING(f'⚠️ SQL 실행 오류 (이미 삭제되었을 수 있음): {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 테이블 삭제 중 예상치 못한 오류 발생: {e}'))
            return

        self._guidance_next_steps()

    def _guidance_next_steps(self):
        """삭제 후 다음 필수 조치 사항 안내"""
        app_name = 'TheaterWinBook'  # 실제 앱 이름 확인

        self.stdout.write(self.style.WARNING('\n----------------------------------------'))
        self.stdout.write(self.style.WARNING('🚀 다음 필수 조치 사항'))
        self.stdout.write(self.style.WARNING('----------------------------------------'))
        self.stdout.write(
            f"1. **마이그레이션 파일 정리:** '{app_name}/migrations/' 폴더에서 0001_initial.py를 제외한 모든 파일을 삭제합니다."
        )
        self.stdout.write("2. **새 마이그레이션 파일 생성:**")
        self.stdout.write(self.style.SUCCESS(f'   $ python manage.py makemigrations {app_name}'))
        self.stdout.write("3. **새 테이블 적용:**")
        self.stdout.write(self.style.SUCCESS('   $ python manage.py migrate'))
        self.stdout.write('\n이제 새로운 Ticker 모델 구조로 데이터 수집을 시작할 수 있습니다.')