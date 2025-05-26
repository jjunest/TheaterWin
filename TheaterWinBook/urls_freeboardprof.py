# from django.conf.urls import include, url
from django.urls import include, path, re_path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # # 게시판 작성 시 6개 페이지 필요 : list / write (원글+답글) / delete / modify / detail
    path(r'^freeBoardprof_list/$', views.freeBoardprof_list, name='freeBoardprof_list'),
    path(r'^freeBoardprof_write/$', views.freeBoardprof_write, name='freeBoardprof_write'),
    # # # 답글을 의미한다.
    path(r'^freeBoardprof_write/(?P<freeBoardprof_pk>\d+)/$', views.freeBoardprof_write, name='freeBoardprof_write'),
    path(r'^freeBoardprof_delete/$', views.freeBoardprof_delete, name='freeBoardprof_delete'),
    path(r'^freeBoardprof_modify/$', views.freeBoardprof_modify, name='freeBoardprof_modify'),
    path(r'^freeBoardprof_detail/$', views.freeBoardprof_detail, name='freeBoardprof_detail'),
    path(r'^freeBoardprof_detail/(?P<freeBoardprof_pk>\d+)/$', views.freeBoardprof_detail, name='freeBoardprof_detail'),
    # freeBoardprof_thumb
    path(r'^ajax/freeBoardprof_thumb_ajax/$', views.freeBoardprof_thumb_ajax, name='freeBoardprof_thumb_ajax'),
    # freeBoardprof_reply
    path(r'^ajax/freeBoardprof_content_reply_write_ajax/$', views.freeBoardprof_content_reply_write_ajax, name='freeBoardprof_content_reply_write_ajax'),
    path(r'^freeBoardprof_reply_delete/$', views.freeBoardprof_reply_delete, name='freeBoardprof_reply_delete'),
    path(r'^freeBoardprof_reply_modify/$', views.freeBoardprof_reply_modify, name='freeBoardprof_reply_modify'),
    path(r'^freeBoardprof_re_reply_write_ajax/$', views.freeBoardprof_re_reply_write_ajax, name='freeBoardprof_re_reply_write_ajax'),
    # 본문 수정을 위한 usercheck
    path(r'^freeBoardprof_usercheck/$', views.freeBoardprof_usercheck, name='freeBoardprof_usercheck'),

]
