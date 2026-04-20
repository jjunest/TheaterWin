# Django > models_stocks_kr.py

from django.db import models
from django.utils import timezone


class StocksKrList(models.Model):
    """한국 주식 종목 리스트 (코인의 CoinsUpbitList에 대응)"""
    id = models.AutoField(primary_key=True)
    stock_code = models.CharField(max_length=20, unique=True, verbose_name="종목코드")  # 예: 005930
    stock_name = models.CharField(max_length=50, verbose_name="종목명")
    market_type = models.CharField(max_length=10, verbose_name="시장구분")  # KOSPI, KOSDAQ, KONEX
    industry = models.CharField(max_length=50, null=True, blank=True, verbose_name="업종")
    is_active = models.BooleanField(default=True)
    bat_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'StocksKrList'

    def __str__(self):
        return f"{self.stock_name} ({self.stock_code})"


class StocksKrCandle(models.Model):
    """주식 일봉 데이터 (코인의 CoinsUpbitCandle에 대응)"""
    id = models.AutoField(primary_key=True)
    stock_code = models.ForeignKey(
        'StocksKrList',
        on_delete=models.CASCADE,
        to_field='stock_code',
        db_column='stock_code'
    )
    date = models.DateField(db_index=True)
    open_price = models.DecimalField(max_digits=20, decimal_places=2)
    high_price = models.DecimalField(max_digits=20, decimal_places=2)
    low_price = models.DecimalField(max_digits=20, decimal_places=2)
    close_price = models.DecimalField(max_digits=20, decimal_places=2)
    volume = models.BigIntegerField()  # 주식은 거래량이 정수형태가 많음
    trade_value = models.BigIntegerField(null=True, blank=True)  # 거래대금

    # 퀀트 분석용 추가 필드
    change_rate = models.DecimalField(max_digits=10, decimal_places=5, null=True)

    class Meta:
        db_table = 'StocksKrCandle'
        unique_together = (('stock_code', 'date'),)
        ordering = ['-date']


class StocksKrTicker(models.Model):
    """
    """
    id = models.AutoField(primary_key=True)

    # 외래키 연결 (StocksKrList의 stock_code 참조)
    stock_code = models.ForeignKey(
        'StocksKrList',
        on_delete=models.CASCADE,
        to_field='stock_code',
        db_column='stock_code'
    )

    bat_time = models.DateTimeField(default=timezone.now, db_index=True)

    # 주요 가격 정보
    ticker_close_price = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='현재가')
    ticker_open_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    ticker_high_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    ticker_low_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    ticker_prev_close = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    # 변동 지표
    ticker_change_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    ticker_change_rate = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)

    # 거래량 및 거래대금
    ticker_volume = models.BigIntegerField(null=True, blank=True, verbose_name='당일 거래량')
    ticker_trade_value = models.BigIntegerField(null=True, blank=True, verbose_name='당일 거래대금')

    # 주식 특화 지표 (네이버 API 제공 데이터)
    market_cap = models.BigIntegerField(null=True, blank=True, verbose_name='시가총액')
    market_cap_rank = models.IntegerField(null=True, blank=True, verbose_name='시총순위')
    foreign_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='외인소진율')

    class Meta:
        db_table = 'stocks_kr_ticker'
        unique_together = (('stock_code', 'bat_time'),)
        ordering = ['-bat_time']

    def __str__(self):
        return f'{self.stock_code.stock_code} - {self.ticker_close_price}'