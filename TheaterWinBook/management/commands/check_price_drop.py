# TheaterWinBook/management/commands/check_price_drop.py
from django.core.management.base import BaseCommand
from ...models_coins import CoinsUpbitTicker
from ...utils_push import send_push_notification
from decimal import Decimal


class Command(BaseCommand):
    help = '전일 대비 5% 이상 하락한 코인 찾아서 알림 보내기'

    def handle(self, *args, **kwargs):
        # 1. 활성화된 최신 티커들 가져오기 (로직 단순화)
        # 실제로는 코인별로 가장 최신 데이터 1개씩만 가져와야 함 (distinct 등 활용)
        tickers = CoinsUpbitTicker.objects.order_by('-bat_time')[:100]

        # [테스트용] 내 앱의 FCM 토큰 (3단계에서 앱 실행 후 로그에서 복사해서 여기에 넣으세요)
        MY_DEVICE_TOKEN = "여기에_앱에서_나온_토큰을_넣어야_합니다"

        target_coins = []

        print("🔍 코인 하락률 점검 시작...")
        for ticker in tickers:
            # 전일 종가 대비 등락률이 -5% 이하인지 확인
            # ticker_signed_change_rate는 소수점 (예: -0.05)
            if ticker.ticker_signed_change_rate and ticker.ticker_signed_change_rate <= Decimal('-0.05'):
                coin_name = ticker.coins_code.coins_name_kor
                rate = ticker.ticker_signed_change_rate * 100
                target_coins.append(f"{coin_name}({rate:.2f}%)")

        if target_coins:
            message_body = ", ".join(target_coins) + " 급락 발생!"
            print(f"📉 알림 발송 중: {message_body}")

            # 푸시 발송
            send_push_notification(
                token=MY_DEVICE_TOKEN,
                title="⚠️ 코인 급락 경보",
                body=message_body
            )
        else:
            print("✅ 5% 이상 하락한 코인이 없습니다.")