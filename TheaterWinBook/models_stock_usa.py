# Django > models_stocks_us.py

from django.db import models
from django.utils import timezone


class StocksUsList(models.Model):
    """미국 주식 종목 리스트 (NASDAQ, NYSE, AMEX)"""
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20, unique=True, verbose_name="티커")  # AAPL, TSLA
    name_en = models.CharField(max_length=200, verbose_name="영문 종목명")
    name_ko = models.CharField(max_length=200, null=True, blank=True, verbose_name="한글 종목명")
    market = models.CharField(max_length=20, verbose_name="시장구분")  # NASDAQ, NYSE, AMEX
    industry = models.CharField(max_length=100, null=True, blank=True, verbose_name="업종")
    sector = models.CharField(max_length=100, null=True, blank=True, verbose_name="섹터")
    is_active = models.BooleanField(default=True)
    bat_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'StocksUsList'

    def __str__(self):
        return f"{self.symbol} ({self.name_ko or self.name_en})"


class StocksUsCandle(models.Model):
    """미국 주식 일봉 데이터"""
    id = models.AutoField(primary_key=True)
    symbol = models.ForeignKey(
        'StocksUsList',
        on_delete=models.CASCADE,
        to_field='symbol',
        db_column='symbol'
    )
    date = models.DateField(db_index=True)
    open_price = models.DecimalField(max_digits=20, decimal_places=4)  # 미국주는 소수점 4자리까지 고려
    high_price = models.DecimalField(max_digits=20, decimal_places=4)
    low_price = models.DecimalField(max_digits=20, decimal_places=4)
    close_price = models.DecimalField(max_digits=20, decimal_places=4)
    adj_close = models.DecimalField(max_digits=20, decimal_places=4, null=True)  # 수정주가 중요
    volume = models.BigIntegerField()

    class Meta:
        db_table = 'StocksUsCandle'
        unique_together = (('symbol', 'date'),)
        ordering = ['-date']


class StocksUsTicker(models.Model):
    """미국 주식 현재가 및 주요 지표 (실시간성 데이터)"""
    id = models.AutoField(primary_key=True)
    symbol = models.ForeignKey(
        'StocksUsList',
        on_delete=models.CASCADE,
        to_field='symbol',
        db_column='symbol'
    )
    bat_time = models.DateTimeField(default=timezone.now, db_index=True)

    price = models.DecimalField(max_digits=20, decimal_places=4)
    change_rate = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    volume = models.BigIntegerField(null=True)
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, null=True)  # 미국 시총은 매우 큼

    class Meta:
        db_table = 'stocks_us_ticker'
        unique_together = (('symbol', 'bat_time'),)
        ordering = ['-bat_time']