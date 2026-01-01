import requests
import time
import traceback
import os
from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings

# 모델 임포트
from TheaterWinBook.models_stock_korea import StocksKrList, StocksKrTicker


def send_notification_telegram(message, level="INFO"):
    """텔레그램 알림 헬퍼 (기존 로직 유지)"""
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        API_URL = f"https://api.telegram.org/bot{token}/sendMessage"

        tag = {"FATAL": "🚨 [치명적 오류] 🚨\n", "ERROR": "❌ [데이터 오류]\n", "WARNING": "⚠️ [경고]\n"}.get(level, "")
        full_message = tag + message
        params = {'chat_id': chat_id, 'text': full_message, 'parse_mode': 'Markdown'}

        requests.post(API_URL, data=params, timeout=5)
    except:
        pass


class Command(BaseCommand):
    help = '네이버 실시간 API를 사용하여 모든 활성 주식의 Ticker 데이터를 수집합니다.'

    DATA_RETENTION_DAYS = 7  # 주식 데이터는 7일간 보관

    def clean_decimal(self, value):
        """'7,245' 같은 문자열에서 콤마 제거 후 Decimal 변환"""
        if not value: return Decimal('0')
        try:
            return Decimal(str(value).replace(',', ''))
        except:
            return Decimal('0')

    def clean_volume(self, value):
        """'1,079' 문자열을 정수로 변환"""
        if not value: return 0
        try:
            return int(str(value).replace(',', ''))
        except:
            return 0

    def clean_trade_value(self, value):
        """'8백만', '1,200억' 등 한글 단위를 숫자로 변환"""
        if not value: return 0
        value = str(value).replace(',', '')
        try:
            if '억' in value:
                return int(float(value.replace('억', '')) * 100_000_000)
            elif '백만' in value:
                return int(float(value.replace('백만', '')) * 1_000_000)
            return int(value)
        except:
            return 0

    def handle(self, *args, **options):
        command_file_name = os.path.basename(__file__)
        start_time = timezone.now()
        self.stdout.write(self.style.SUCCESS(f'[{start_time}] 주식 Ticker 수집 시작...'))

        # 1. 수집 대상 가져오기
        active_stocks = StocksKrList.objects.filter(is_active=True)
        if not active_stocks.exists():
            return

        ticker_objects = []
        batch_info_header = f"**파일:** `{command_file_name}`\n**시간:** `{start_time}`\n---"

        # 2. 개별 종목 API 요청 (네이버는 개별 호출이 가장 정확함)
        for stock in active_stocks:
            ticker_code = stock.stock_code
            # API URL: polling.finance.naver.com 사용
            api_url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{ticker_code}"

            try:
                response = requests.get(api_url, timeout=5)
                response.raise_for_status()
                data_root = response.json()

                if not data_root.get('datas'):
                    continue

                item = data_root['datas'][0]

                # 객체 생성
                ticker_objects.append(
                    StocksKrTicker(
                        stock_code=stock,
                        bat_time=start_time,
                        ticker_close_price=self.clean_decimal(item.get('closePrice')),
                        ticker_open_price=self.clean_decimal(item.get('openPrice')),
                        ticker_high_price=self.clean_decimal(item.get('highPrice')),
                        ticker_low_price=self.clean_decimal(item.get('lowPrice')),
                        ticker_prev_close=self.clean_decimal(item.get('closePrice')) - self.clean_decimal(
                            item.get('compareToPreviousClosePrice')),
                        ticker_change_price=self.clean_decimal(item.get('compareToPreviousClosePrice')),
                        ticker_change_rate=self.clean_decimal(item.get('fluctuationsRatio')) / Decimal('100'),
                        ticker_volume=self.clean_volume(item.get('accumulatedTradingVolume')),
                        ticker_trade_value=self.clean_trade_value(item.get('accumulatedTradingValue')),
                    )
                )
                # 네이버 차단 방지를 위한 미세 딜레이 (종목이 많을 경우 0.05~0.1 조절)
                time.sleep(0.05)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error {ticker_code}: {e}"))
                continue

        # 3. Bulk Create 저장
        try:
            with transaction.atomic():
                if ticker_objects:
                    StocksKrTicker.objects.bulk_create(ticker_objects, batch_size=500)
                    self.stdout.write(self.style.SUCCESS(f"Saved {len(ticker_objects)} stocks."))
        except Exception as e:
            error_msg = f"주식 Ticker 저장 실패: {e}\n{traceback.format_exc()[:500]}"
            send_notification_telegram(f"{batch_info_header}\n{error_msg}", level="FATAL")
            return

        # 4. 오래된 데이터 삭제
        self.delete_old_data(start_time)

    def delete_old_data(self, current_time):
        threshold = current_time - timedelta(days=self.DATA_RETENTION_DAYS)
        deleted, _ = StocksKrTicker.objects.filter(bat_time__lt=threshold).delete()
        if deleted > 0:
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} old records."))