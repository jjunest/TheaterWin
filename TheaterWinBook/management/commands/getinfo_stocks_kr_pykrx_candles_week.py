import os
import time
import traceback
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np
import requests
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db import transaction

# pykrx 라이브러리 (국내 주식 데이터의 표준)
from pykrx import stock as krx

# 모델 임포트 (경로는 프로젝트 설정에 맞춰 확인해 주세요)
from TheaterWinBook.models_stock_korea import StocksKrList, StocksKrCandle


def send_notification_telegram(message, level="INFO"):
    """텔레그램 알림 헬퍼 함수"""
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        if not token or not chat_id:
            return

        API_URL = f"https://api.telegram.org/bot{token}/sendMessage"
        tag = {
            "FATAL": "🚨 [Pykrx-치명적] 🚨\n",
            "ERROR": "❌ [Pykrx-오류] ❌\n",
            "SUCCESS": "✅ [Pykrx-완료] ✅\n"
        }.get(level, "ℹ️ [정보]\n")

        full_message = tag + message
        requests.post(
            API_URL,
            data={'chat_id': chat_id, 'text': full_message[:3900], 'parse_mode': 'Markdown'},
            timeout=5
        )
    except Exception:
        pass


class Command(BaseCommand):
    help = 'Pykrx를 사용하여 ETF 포함 모든 국내 주식의 캔들(OHLCV) 데이터를 수집합니다.'

    def to_decimal(self, val):
        """안전하게 Decimal 타입으로 변환하는 내부 메서드"""
        if val is None or pd.isna(val):
            return Decimal('0.0')
        try:
            # float나 int를 문자열로 바꾼 뒤 Decimal로 변환하는 것이 가장 안전함
            return Decimal(str(val))
        except (ValueError, TypeError):
            return Decimal('0.0')

    def handle(self, *args, **options):
        start_time = timezone.now()

        # 1. 수집 기간 설정 (최근 14일치 데이터를 동기화)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')

        # 2. DB에서 수집 대상(활성 상태 종목) 로드
        active_stocks = StocksKrList.objects.filter(is_active=True)
        total_active = active_stocks.count()

        self.stdout.write(self.style.SUCCESS(f"🚀 Pykrx 국내 데이터 수집 시작: {start_date} ~ {end_date}"))

        processed_count = 0
        failed_stocks = []

        for stock_obj in active_stocks:
            ticker = stock_obj.stock_code

            try:
                # 3. Pykrx를 통해 OHLCV 데이터 호출
                df = krx.get_market_ohlcv_by_date(fromdate=start_date, todate=end_date, ticker=ticker)

                if df.empty:
                    continue

                # 4. 데이터 컬럼명 표준화 및 정제
                df = df.rename(columns={
                    '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close',
                    '거래량': 'Volume', '거래대금': 'Value', '등락률': 'Change'
                }).replace({np.nan: 0.0})

                df = df.reset_index()  # 인덱스였던 '날짜'를 컬럼으로 변환

                # 5. DB 저장 (종목별 단일 트랜잭션 처리)
                with transaction.atomic():
                    for _, row in df.iterrows():
                        # 날짜 컬럼명 대응 (버전에 따라 '날짜' 혹은 'Date')
                        c_date = row.get('날짜') or row.get('Date')
                        if pd.isna(c_date):
                            continue

                        # 거래량이 0인 날(상장 전, 정지, 휴장 등)은 데이터 적재에서 제외
                        vol = int(row.get('Volume', 0))
                        if vol == 0:
                            continue

                        # update_or_create를 사용하여 기존 데이터는 갱신, 없으면 생성
                        StocksKrCandle.objects.update_or_create(
                            stock_code=stock_obj,
                            date=c_date.date() if hasattr(c_date, 'date') else c_date,
                            defaults={
                                'open_price': self.to_decimal(row.get('Open')),
                                'high_price': self.to_decimal(row.get('High')),
                                'low_price': self.to_decimal(row.get('Low')),
                                'close_price': self.to_decimal(row.get('Close')),
                                'volume': vol,
                                'trade_value': int(row.get('Value', 0)),
                                # 등락률은 % 단위이므로 100으로 나눔
                                'change_rate': self.to_decimal(row.get('Change')) / Decimal('100.0'),
                            }
                        )

                processed_count += 1

                # 50개 종목마다 로그 출력하여 진행 상황 확인
                if processed_count % 50 == 0:
                    self.stdout.write(f"📊 진행 상황: {processed_count}/{total_active} 종목 완료")

                # 서버 과부하 방지를 위한 미세한 대기 시간
                time.sleep(0.05)

            except Exception as e:
                # 개별 종목 실패 시 로그 남기고 다음 종목으로 진행
                self.stdout.write(self.style.ERROR(f"❌ 오류 발생 [{ticker}]: {str(e)}"))
                failed_stocks.append(ticker)
                continue

        # 6. 전체 결과 요약 및 텔레그램 알림
        duration = (timezone.now() - start_time).total_seconds()
        summary = (
            f"**Pykrx 데이터 수집 완료**\n"
            f"- 대상 종목: {total_active}개\n"
            f"- 성공: {processed_count}개 / 실패: {len(failed_stocks)}개\n"
            f"- 소요 시간: {duration / 60:.1f}분"
        )

        if failed_stocks:
            summary += f"\n- 실패 티커: `{', '.join(failed_stocks[:10])}`"
            if len(failed_stocks) > 10: summary += " 외..."

        self.stdout.write(self.style.SUCCESS(f"✅ 배치 완료: {summary}"))
        send_notification_telegram(summary, level="SUCCESS")