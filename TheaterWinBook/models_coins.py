from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
# from django.utils.datetime_safe import datetime
from datetime import datetime
from tinymce import models as tinymce_models


class CoinsUpbitList(models.Model):
    id = models.AutoField(primary_key=True)  # id 필드는 Django가 자동으로 생성하므로 삭제하거나 그대로 둡니다. ID 필드를 기본 키로 명시적으로 설정
    bat_time = models.DateTimeField(null=True, blank=True)
    info_date = models.DateField()
    coins_code = models.CharField(max_length=10, unique=True)
    coins_name_kor = models.CharField(max_length=10)
    coins_name_eng = models.CharField(max_length=10)
    warning = models.BooleanField()
    price_fluctuations = models.BooleanField()
    trading_volume_soaring = models.BooleanField()
    deposit_amount_soaring = models.BooleanField()
    global_price_differences = models.BooleanField()
    concentration_of_small_accounts = models.BooleanField()

    etc1_string = models.CharField(max_length=1, null=True, blank=True)
    etc2_string = models.CharField(max_length=1, null=True, blank=True)
    etc3_string = models.CharField(max_length=1, null=True, blank=True)
    etc4_string = models.CharField(max_length=1, null=True, blank=True)
    etc_varchar = models.CharField(max_length=1, null=True, blank=True)

    etc1_int = models.SmallIntegerField(null=True, blank=True)
    etc2_int = models.SmallIntegerField(null=True, blank=True)
    etc3_int = models.SmallIntegerField(null=True, blank=True)
    etc4_int = models.SmallIntegerField(null=True, blank=True)
    etc5_int = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        # DB 테이블명 지정 (일반적으로 Django가 자동으로 생성하지만 명시적으로 지정하는 것이 좋습니다.)
        db_table = 'coins_upbit_list'
        # PK(Primary Key)가 여러 개인 경우 composite key 설정
        unique_together = (('info_date', 'coins_code'),)

    def __str__(self):
        return f'{self.coins_name_kor} ({self.coins_code})'



class CoinsUpbitCandle(models.Model):
    # 기본 키와 데이터 수집 시간
    id = models.AutoField(primary_key=True)
    bat_time = models.DateTimeField(null=True, blank=True)

    # 코인 정보 연결 (CoinsUpbitList의 coins_code 필드와 연결)
    coins_code = models.ForeignKey(
        'CoinsUpbitList',
        on_delete=models.CASCADE,
        to_field='coins_code',
        db_column='coins_code'
    )

    # 캔들 시간 및 가격 데이터
    coin_candle_datetime_kst = models.DateTimeField()
    coin_opening_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    coin_high_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    coin_low_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    coin_closing_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    coin_trade_price = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    coin_trade_volume = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)

    # 기타 여유 필드
    etc1_string = models.CharField(max_length=1, null=True, blank=True)
    etc2_string = models.CharField(max_length=1, null=True, blank=True)
    etc3_string = models.CharField(max_length=1, null=True, blank=True)
    etc_varchar = models.CharField(max_length=1, null=True, blank=True)
    etc1_int = models.SmallIntegerField(null=True, blank=True)
    etc2_int = models.SmallIntegerField(null=True, blank=True)
    etc3_int = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'coins_upbit_candle'
        unique_together = (('coins_code', 'coin_candle_datetime_kst'),)
        ordering = ['-coin_candle_datetime_kst']

    def __str__(self):
        return f'{self.coins_code.coins_code} - {self.coin_candle_datetime_kst}'




