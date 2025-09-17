#TheaterWinBook/management/commands/dbquery_delete.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from TheaterWinBook.models_coins import CoinsUpbitList, CoinsUpbitCandle


class Command(BaseCommand):
    help = 'Deletes old data from the CoinsUpbitCandle table that are older than 30 days.'

    def handle(self, *args, **kwargs):
        # 현재 시간에서 30일을 뺀 기준 시간을 계산합니다.
        # cutoff_date = timezone.now() - timedelta(days=30)

        # 기준 시간보다 오래된 데이터를 필터링하여 삭제합니다.
        # delete() 메서드는 삭제된 row의 수와, 삭제된 객체 타입별 수를 튜플로 반환합니다.
        # deleted_count, _ = CoinsUpbitCandle.objects.filter(created_at__lt=cutoff_date).delete()

        # 테이블 삭제 명령어
        deleted_count, _ = CoinsUpbitCandle.objects.filter().delete()

        # 사용자에게 성공 메시지를 출력합니다.
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} old candle records.')
        )