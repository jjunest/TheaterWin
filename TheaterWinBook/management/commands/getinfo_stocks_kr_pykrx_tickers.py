import os
import traceback
import time
from datetime import timedelta
from decimal import Decimal

import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

# pykrx 라이브러리
from pykrx import stock as krx

# 모델 임포트 (프로젝트 구조에 맞게 수정 확인)
from TheaterWinBook.models_stock_korea import StocksKrList, StocksKrTicker


class Command(BaseCommand):
    help = '국내 주식 및 ETF의 현재가 및 시가총액(Ticker) 데이터를 수집합니다. (휴장일 자동 대응)'

    def to_decimal(self, val):
        """안전한 Decimal 변환 헬퍼"""
        if val is None or pd.isna(val):
            return Decimal('0.0')
        try:
            return Decimal(str(val))
        except (ValueError, TypeError):
            return Decimal('0.0')

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(self.style.SUCCESS(f"🚀 국내 Ticker 동기화 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}"))

        try:
            # 1. 활성 종목 리스트 로드 (매핑용)
            active_stocks = StocksKrList.objects.filter(is_active=True)
            stock_map = {s.stock_code: s for s in active_stocks}

            if not stock_map:
                self.stdout.write(self.style.WARNING("수집할 활성 종목이 DB에 없습니다."))
                return

            # 2. 최근 영업일 데이터 찾기 (KeyError 방지 핵심 로직)
            # 오늘부터 최대 10일 전까지 거슬러 올라가며 데이터가 있는 날을 찾습니다.
            search_date = start_time
            df_all = pd.DataFrame()
            target_date_str = ""

            for i in range(10):
                temp_date_str = search_date.strftime('%Y%m%d')
                try:
                    # KOSPI, KOSDAQ 시세 호출
                    df_kospi = krx.get_market_ohlcv(temp_date_str, market="KOSPI")
                    df_kosdaq = krx.get_market_ohlcv(temp_date_str, market="KOSDAQ")

                    # 데이터가 정상적으로 있으면 (컬럼이 존재하면) 합치기
                    if not df_kospi.empty and '종가' in df_kospi.columns:
                        df_all = pd.concat([df_kospi, df_kosdaq])
                        target_date_str = temp_date_str
                        self.stdout.write(self.style.SUCCESS(f"✅ {target_date_str} 영업일 데이터를 발견했습니다."))
                        break
                except Exception:
                    # 데이터가 없는 날(KeyError 등)은 무시하고 하루 전으로
                    pass

                search_date -= timedelta(days=1)

            if df_all.empty:
                self.stdout.write(self.style.ERROR("❌ 최근 10일 이내에 유효한 영업일 데이터를 찾을 수 없습니다."))
                return

            # 3. 해당 날짜의 시가총액 데이터 추가 호출
            df_cap = krx.get_market_cap(target_date_str)

            # 시세 데이터와 시가총액 데이터를 티커(Index) 기준으로 병합
            df_final = pd.merge(df_all, df_cap, left_index=True, right_index=True, how='inner').reset_index()

            ticker_objects = []

            # 4. 데이터 매핑 및 객체 생성
            for _, row in df_final.iterrows():
                ticker = row['티커']

                if ticker in stock_map:
                    stock_obj = stock_map[ticker]

                    # 현재가(종가)가 0인 경우는 상장폐지 혹은 정지이므로 제외
                    price = self.to_decimal(row.get('종가', 0))
                    if price == 0:
                        continue

                    ticker_objects.append(
                        StocksKrTicker(
                            stock_code=stock_obj,
                            bat_time=start_time,  # 기록 시점은 배치 실행 시간
                            ticker_close_price=price,
                            ticker_open_price=self.to_decimal(row.get('시가', 0)),
                            ticker_high_price=self.to_decimal(row.get('고가', 0)),
                            ticker_low_price=self.to_decimal(row.get('저가', 0)),
                            ticker_volume=int(row.get('거래량', 0)),
                            ticker_trade_value=int(row.get('거래대금', 0)),
                            ticker_change_rate=self.to_decimal(row.get('등락률', 0)) / Decimal('100.0'),
                            market_cap=int(row.get('시가총액', 0)),
                        )
                    )

            # 5. DB 저장 (Bulk Create로 속도 극대화)
            with transaction.atomic():
                if ticker_objects:
                    # 데이터가 많으므로 500개씩 끊어서 저장
                    StocksKrTicker.objects.bulk_create(ticker_objects, batch_size=500)

            duration = (timezone.now() - start_time).total_seconds()
            self.stdout.write(self.style.SUCCESS(f"✅ 동기화 완료: {len(ticker_objects)}건 수집 (소요시간: {duration:.2f}s)"))

        except Exception as e:
            error_msg = f"❌ Ticker 배치 중 치명적 오류: {str(e)}"
            self.stdout.write(self.style.ERROR(error_msg))
            print(traceback.format_exc())