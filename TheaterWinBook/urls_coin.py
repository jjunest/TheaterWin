# from django.conf.urls import include, url
from django.urls import include, path, re_path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # # 게시판 작성 시 6개 페이지 필요 : list / write (원글+답글) / delete / modify / detail
    # path(r'^freeBoard_list/$', views.freeBoard_list, name='freeBoard_list'),
    # path(r'^freeBoard_write/$', views.freeBoard_write, name='freeBoard_write'),
    # # # # 답글을 의미한다.
    # path(r'^freeBoard_write/(?P<freeBoard_pk>\d+)/$', views.freeBoard_write, name='freeBoard_write'),
    # path(r'^freeBoard_delete/$', views.freeBoard_delete, name='freeBoard_delete'),
    # path(r'^freeBoard_modify/$', views.freeBoard_modify, name='freeBoard_modify'),
    # path(r'^freeBoard_detail/$', views.freeBoard_detail, name='freeBoard_detail'),
    # path(r'^freeBoard_detail/(?P<freeBoard_pk>\d+)/$', views.freeBoard_detail, name='freeBoard_detail'),
    # # freeBoard_thumb
    # path(r'^ajax/freeBoard_thumb_ajax/$', views.freeBoard_thumb_ajax, name='freeBoard_thumb_ajax'),
    # # freeBoard_reply
    # path(r'^ajax/freeBoard_content_reply_write_ajax/$', views.freeBoard_content_reply_write_ajax, name='freeBoard_content_reply_write_ajax'),
    # path(r'^freeBoard_reply_delete/$', views.freeBoard_reply_delete, name='freeBoard_reply_delete'),
    # path(r'^freeBoard_reply_modify/$', views.freeBoard_reply_modify, name='freeBoard_reply_modify'),
    # path(r'^freeBoard_re_reply_write_ajax/$', views.freeBoard_re_reply_write_ajax, name='freeBoard_re_reply_write_ajax'),
    # # 본문 수정을 위한 usercheck
    # path(r'^freeBoard_usercheck/$', views.freeBoard_usercheck, name='freeBoard_usercheck'),

    # 게시판 목록, 작성, 수정, 삭제, 상세보기
    path("coin_list/", views.coin_list, name="coin_list"),
    path("coin_rank/", views.coin_rank, name="coin_rank"),

    path("template_250705/", views.template_250705, name="template_250705"),
    # 1. 알람 설정 팝업 (기존)
    # path('coin/alarm/setting/<str:coin_ticker>/', views.coin_alarm_setting_pop, name='coin_alarm_setting_pop'),

    # 2. **코인 차트 팝업 (새로 추가)** 🚀
    path('coin/chart/<str:coin_ticker>/', views.coin_chart_pop, name='coin_chart_pop'),

    # 🚨 코인 상세 페이지 URL 패턴 추가
    path('coin/detail/<str:coin_code>/', views.coin_detail_view, name='coin_detail'),

    path('coin/compare/', views.coin_compare_view, name='coin_compare_view'),

    # urls.py에 정의되어야 함
    path('get_coin_candle/<str:coin_code>/', views.get_coin_candle, name='get_coin_candle'),

]
