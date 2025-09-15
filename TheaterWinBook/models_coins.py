from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
# from django.utils.datetime_safe import datetime
from datetime import datetime
from tinymce import models as tinymce_models


class CoinsUpbitList(models.Model):
    id = models.AutoField(primary_key=True)  # ID 필드를 기본 키로 명시적으로 설정
    bat_time = models.DateTimeField(verbose_name='배치시간', auto_now=True)
    info_date = models.DateField(verbose_name='기준시간')  # primary_key=True 제거
    coins_code = models.CharField(max_length=10, verbose_name='코인종목코드', unique=True)
    coins_name_kor = models.CharField(max_length=10, verbose_name='코인한글명')
    coins_name_eng = models.CharField(max_length=10, verbose_name='코인영문명')
    warning = models.BooleanField(verbose_name='투자유의')
    price_fluctuations = models.BooleanField(verbose_name='급격한가격변동')
    trading_volume_soaring = models.BooleanField(verbose_name='거래량급등')
    deposit_amount_soaring = models.BooleanField(verbose_name='입금량급증')
    global_price_differences = models.BooleanField(verbose_name='전역세차이')
    concentration_of_small_accounts = models.BooleanField(verbose_name='소수계정집중')

    # 여유분 필드는 필요시 사용합니다.
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


