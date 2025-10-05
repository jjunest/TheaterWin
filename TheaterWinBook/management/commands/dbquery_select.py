#TheaterWinBook/management/commands/dbquery_delete.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from TheaterWinBook.models_coins import CoinsUpbitList, CoinsUpbitCandle


class Command(BaseCommand):
    help = 'Select query from Model'

    def handle(self, *args, **kwargs):
        # 현재 시간에서 30일을 뺀 기준 시간을 계산합니다.
        # cutoff_date = timezone.now() - timedelta(days=30)

        # 2. 데이터 조회 (SELECT)
        # 전체 데이터 중 10개만 조회
        recent_data = CoinsUpbitCandle.objects.all().order_by('-id')[:10]

        # 3. 데이터 출력 및 확인
        # for item in recent_data:
            # 객체의 모든 필드를 포함하는 내부 딕셔너리를 출력
            # print(item.__dict__)


        # 예: 요청받은 코인 티커가 'KRW-BTC'라고 가정
        test_ticker = 'KRW-WAVES'

        # 쿼리 실행
        test_data = CoinsUpbitCandle.objects.filter(coins_code__coins_code=test_ticker)

        # 결과 확인
        print(f"테스트 Ticker: {test_ticker}, 조회 건수: {test_data.count()}")
