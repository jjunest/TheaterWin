from django.urls import include, path, re_path
# from django.conf.urls import include, url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # # 게시판 작성 시 6개 페이지 필요 : list / write (원글+답글) / delete / modify / detail

    path(r'^freeBoardstock_list/$', views.freeBoardstock_list, name='freeBoardstock_list'),
    path(r'^freeBoardstock_write/$', views.freeBoardstock_write, name='freeBoardstock_write'),
    # # # 답글을 의미한다.
    path(r'^freeBoardstock_write/(?P<freeBoardstock_pk>\d+)/$', views.freeBoardstock_write, name='freeBoardstock_write'),
    path(r'^freeBoardstock_delete/$', views.freeBoardstock_delete, name='freeBoardstock_delete'),
    path(r'^freeBoardstock_modify/$', views.freeBoardstock_modify, name='freeBoardstock_modify'),
    path(r'^freeBoardstock_detail/$', views.freeBoardstock_detail, name='freeBoardstock_detail'),
    path(r'^freeBoardstock_detail/(?P<freeBoardstock_pk>\d+)/$', views.freeBoardstock_detail, name='freeBoardstock_detail'),
    # freeBoardstock_thumb
    path(r'^ajax/freeBoardstock_thumb_ajax/$', views.freeBoardstock_thumb_ajax, name='freeBoardstock_thumb_ajax'),
    # freeBoardstock_reply
    path(r'^ajax/freeBoardstock_content_reply_write_ajax/$', views.freeBoardstock_content_reply_write_ajax, name='freeBoardstock_content_reply_write_ajax'),
    path(r'^freeBoardstock_reply_delete/$', views.freeBoardstock_reply_delete, name='freeBoardstock_reply_delete'),
    path(r'^freeBoardstock_reply_modify/$', views.freeBoardstock_reply_modify, name='freeBoardstock_reply_modify'),
    path(r'^freeBoardstock_re_reply_write_ajax/$', views.freeBoardstock_re_reply_write_ajax, name='freeBoardstock_re_reply_write_ajax'),
    # 본문 수정을 위한 usercheck
    path(r'^freeBoardstock_usercheck/$', views.freeBoardstock_usercheck, name='freeBoardstock_usercheck'),

]
