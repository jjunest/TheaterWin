import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import pandas as pd

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

import FinanceDataReader as fdr
from TheaterWinBook.models_stock_usa import StocksUsList, StocksUsCandle
from TheaterWinBook.utils_telegram import send_notification_telegram


class Command(BaseCommand):
    help = '미국 주식 캔들 수집 (인덱스 직접 참조 및 필드 매핑 강화 버전)'

    def convert_ticker(self, symbol):
        """야후 파이낸스 규격으로 티커 변환"""
        return symbol.replace(' PR ', '-P').replace('.', '-').replace(' ', '-')

    def handle(self, *args, **options):
        start_time = timezone.now()
        # 데이터 유실 방지를 위해 기간을 넉넉히 21일로 설정
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=21)).strftime('%Y-%m-%d')

        active_stocks = StocksUsList.objects.filter(is_active=True).order_by('symbol')
        total_active = active_stocks.count()

        self.stdout.write(self.style.SUCCESS(f"🚀 미국 주식 수집 시작 ({total_active} 종목)"))

        processed_count = 0
        success_save_count = 0
        failed_stocks = []


        for stock_obj in active_stocks:
            search_symbol = self.convert_ticker(stock_obj.symbol)

            try:
                # print("this is us fdr search_symbol:", search_symbol)
                df = fdr.DataReader(search_symbol, start_date, end_date)
                # print("this is us fdr symbol:",df)
                if df is None or df.empty:
                    continue

                # [CTO 핵심 수정]

                # 2. 인덱스(날짜)를 컬럼으로 변환
                df.index.name = 'date_col'
                # df = df.reset_index() 대신 인덱스 이름을 명시적으로 'date_col'로 지정
                df.index.name = 'date_col'
                df = df.reset_index()

                # 모든 컬럼명을 소문자로 통일
                df.columns = [c.lower().replace(' ', '') for c in df.columns]
                with transaction.atomic():
                    for _, row in df.iterrows():
                        # [핵심] date_col 이라는 이름으로 안전하게 가져옴
                        c_date = row.get('date_col')

                        # 만약 여전히 None이라면, 첫 번째 컬럼(인덱스가 변환된 컬럼)을 가져옴
                        if c_date is None:
                            c_date = row.iloc[0]

                            # 디버깅 출력
                        # print(f"파싱된 날짜 데이터: {c_date} / 타입: {type(c_date)}")

                        if pd.isna(c_date):
                            continue  # 여기서 걸리면 데이터 자체가 없는 것

                        # 날짜 변환 로직 (Timestamp 대응)
                        if isinstance(c_date, (pd.Timestamp, datetime)):
                            target_date = c_date.date()
                        else:
                            target_date = pd.to_datetime(c_date).date()

                        # 거래량 확인
                        vol = int(row.get('volume', 0))
                        if vol == 0: continue
                        def to_dec(val):
                            if val is None or pd.isna(val) or val == '': return Decimal('0.0000')
                            return Decimal(str(val))

                        # [CTO 수정] 모델 필드명과 정확히 일치하는지 재확인하세요.
                        # defaults의 key는 모델 필드명이어야 합니다.

                        _, created = StocksUsCandle.objects.update_or_create(
                            symbol=stock_obj,
                            date=target_date,
                            defaults={
                                'open_price': to_dec(row.get('open')),
                                'high_price': to_dec(row.get('high')),
                                'low_price': to_dec(row.get('low')),
                                'close_price': to_dec(row.get('close')),
                                'adj_close': to_dec(row.get('adjclose', row.get('close'))),
                                'volume': vol,
                            }
                        )
                        success_save_count += 1

                processed_count += 1
                if processed_count % 100 == 0:
                    self.stdout.write(f"[{processed_count}/{total_active}] 완료 (누적 저장 데이터: {success_save_count})")

                time.sleep(0.1)

            except Exception as e:
                failed_stocks.append(f"{stock_obj.symbol}")
                continue

        # 최종 보고
        duration = (timezone.now() - start_time).total_seconds()
        summary = (
            f"**미국 주식 캔들 동기화 완료**\n"
            f"- 대상 종목: {total_active}개\n"
            f"- 성공 종목: {processed_count}개\n"
            f"- 실패 종목: {len(failed_stocks)}개\n"
            f"- 총 저장 건수: {success_save_count}건\n"
            f"- 소요시간: {duration / 60:.1f}분"
        )
        send_notification_telegram(summary, level="SUCCESS", category="미국주식")