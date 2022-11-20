from django.conf.urls import include, url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # # 게시판 작성 시 6개 페이지 필요 : list / write (원글+답글) / delete / modify / detail

    url(r'^freeBoardstock_list/$', views.freeBoardstock_list, name='freeBoardstock_list'),
    url(r'^freeBoardstock_write/$', views.freeBoardstock_write, name='freeBoardstock_write'),
    # # # 답글을 의미한다.
    url(r'^freeBoardstock_write/(?P<freeBoardstock_pk>\d+)/$', views.freeBoardstock_write, name='freeBoardstock_write'),
    url(r'^freeBoardstock_delete/$', views.freeBoardstock_delete, name='freeBoardstock_delete'),
    url(r'^freeBoardstock_modify/$', views.freeBoardstock_modify, name='freeBoardstock_modify'),
    url(r'^freeBoardstock_detail/$', views.freeBoardstock_detail, name='freeBoardstock_detail'),
    url(r'^freeBoardstock_detail/(?P<freeBoardstock_pk>\d+)/$', views.freeBoardstock_detail, name='freeBoardstock_detail'),
    # freeBoardstock_thumb
    url(r'^ajax/freeBoardstock_thumb_ajax/$', views.freeBoardstock_thumb_ajax, name='freeBoardstock_thumb_ajax'),
    # freeBoardstock_reply
    url(r'^ajax/freeBoardstock_content_reply_write_ajax/$', views.freeBoardstock_content_reply_write_ajax, name='freeBoardstock_content_reply_write_ajax'),
    url(r'^freeBoardstock_reply_delete/$', views.freeBoardstock_reply_delete, name='freeBoardstock_reply_delete'),
    url(r'^freeBoardstock_reply_modify/$', views.freeBoardstock_reply_modify, name='freeBoardstock_reply_modify'),
    url(r'^freeBoardstock_re_reply_write_ajax/$', views.freeBoardstock_re_reply_write_ajax, name='freeBoardstock_re_reply_write_ajax'),
    # 본문 수정을 위한 usercheck
    url(r'^freeBoardstock_usercheck/$', views.freeBoardstock_usercheck, name='freeBoardstock_usercheck'),

]
