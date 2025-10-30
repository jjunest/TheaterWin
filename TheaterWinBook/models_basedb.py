# Django>models_basedb.py 파일

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class EcosIndicator(models.Model):
    """
    한국은행 ECOS API로부터 수집한 거시 경제 지표 데이터를 저장하는 모델
    """
    # 배치 실행 시점 기록
    bat_time = models.DateTimeField(auto_now=True, verbose_name='배치 저장 시간')

    # ECOS 통계 코드 (예: 030Y001)
    stat_code = models.CharField(max_length=10, verbose_name='통계표 코드')
    # ECOS 항목 코드 (예: 0000001)
    item_code = models.CharField(max_length=15, verbose_name='항목 코드')
    # 데이터 기준 날짜 (Primary Key)
    data_date = models.DateField(verbose_name='기준 날짜')

    # 지표 식별 정보
    indicator_name = models.CharField(max_length=100, verbose_name='지표 이름')
    indicator_unit = models.CharField(max_length=50, verbose_name='지표 단위', default='')

    # 실제 데이터 값
    data_value = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        verbose_name='데이터 값'
    )

    class Meta:
        # 복합 유니크 키 설정: 동일 통계표의 동일 날짜 데이터는 중복 저장 방지 (Upsert 용이)
        unique_together = ('stat_code', 'item_code', 'data_date')
        verbose_name = 'ECOS 거시 지표'
        verbose_name_plural = 'ECOS 거시 지표 목록'

    def __str__(self):
        return f"[{self.stat_code}] {self.indicator_name} ({self.data_date}): {self.data_value}"