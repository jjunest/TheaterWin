from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
# from django.utils.datetime_safe import datetime
from datetime import datetime
from tinymce import models as tinymce_models


class FreeBoardstock(models.Model):
    # 토계부 질문게시판용 필드 모델
    writing_date = models.DateField(default=datetime.now, blank=False)
    freeBoardstock_title = models.CharField(max_length=200, blank=False)
    freeBoardstock_content = tinymce_models.HTMLField(blank=True)
    # isanswer 은 답변이 달렸는지에 대한 필드, 0이면 안 달리고 1이면 달린것이다.
    freeBoardstock_isanswer = models.IntegerField(default=0, blank=False)
    freeBoardstock_hit = models.IntegerField(default=0, blank=False)
    # 계층형 답변 게시물을 위한 필드
    freeBoardstock_groupnum = models.IntegerField(default=0, blank=False)
    freeBoardstock_sequencenum_ingroup = models.IntegerField(default=0, blank=False)
    freeBoardstock_level_ingorup = models.IntegerField(default=0, blank=False)
    # 기타 메모 및 유저 네임 필드
    etc_memo = models.CharField(blank=True, max_length=200)
    user_name = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    def publish(self):
        self.writing_date = timezone.now()
        self.save()

    def __str__(self):
        return self.freeBoardstock_title


class FreeBoardstockInfo(models.Model):
    # 토계부 질문게시판용 필드 모델
    freeBoardstock_fk = models.ForeignKey(FreeBoardstock, on_delete=models.CASCADE, default=1, blank=False)
    freeBoardstock_thumbup = models.IntegerField(default=0, blank=False)
    freeBoardstock_thumbdown = models.IntegerField(default=0, blank=False)
    freeBoardstock_warning = models.IntegerField(default=0, blank=False)
    # CharField 는 무조건 max_length 라는 속성이 추가 되어야 함.
    by_whom = models.ForeignKey(User, on_delete=models.CASCADE, default=1)


class FreeBoardstockReply(models.Model):
    # 토계부 리플용 DB
    writing_date = models.DateField(default=datetime.now, blank=False)
    freeBoardstock_fk = models.ForeignKey(FreeBoardstock, on_delete=models.CASCADE, default=1, blank=False)
    freeBoardstock_reply_content = models.CharField(max_length=200)
    freeBoardstock_reply_thumbup = models.IntegerField(default=0, blank=False)
    freeBoardstock_reply_thumbdown = models.IntegerField(default=0, blank=False)
    freeBoardstock_reply_warning = models.IntegerField(default=0, blank=False)
    # CharField 는 무조건 max_length 라는 속성이 추가 되어야 함.
    by_whom = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    # 계층형 답변 게시물을 위한 필드
    reply_groupnum = models.IntegerField(default=0, blank=False)
    reply_sequencenum_ingroup = models.IntegerField(default=0, blank=False)
    reply_level_ingorup = models.IntegerField(default=0, blank=False)

    def publish(self):
        self.writing_date = timezone.now()
        self.save()



