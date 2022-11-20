from django.conf.urls import include, url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # # 게시판 작성 시 6개 페이지 필요 : list / write (원글+답글) / delete / modify / detail
    url(r'^freeBoardprof_list/$', views.freeBoardprof_list, name='freeBoardprof_list'),
    url(r'^freeBoardprof_write/$', views.freeBoardprof_write, name='freeBoardprof_write'),
    # # # 답글을 의미한다.
    url(r'^freeBoardprof_write/(?P<freeBoardprof_pk>\d+)/$', views.freeBoardprof_write, name='freeBoardprof_write'),
    url(r'^freeBoardprof_delete/$', views.freeBoardprof_delete, name='freeBoardprof_delete'),
    url(r'^freeBoardprof_modify/$', views.freeBoardprof_modify, name='freeBoardprof_modify'),
    url(r'^freeBoardprof_detail/$', views.freeBoardprof_detail, name='freeBoardprof_detail'),
    url(r'^freeBoardprof_detail/(?P<freeBoardprof_pk>\d+)/$', views.freeBoardprof_detail, name='freeBoardprof_detail'),
    # freeBoardprof_thumb
    url(r'^ajax/freeBoardprof_thumb_ajax/$', views.freeBoardprof_thumb_ajax, name='freeBoardprof_thumb_ajax'),
    # freeBoardprof_reply
    url(r'^ajax/freeBoardprof_content_reply_write_ajax/$', views.freeBoardprof_content_reply_write_ajax, name='freeBoardprof_content_reply_write_ajax'),
    url(r'^freeBoardprof_reply_delete/$', views.freeBoardprof_reply_delete, name='freeBoardprof_reply_delete'),
    url(r'^freeBoardprof_reply_modify/$', views.freeBoardprof_reply_modify, name='freeBoardprof_reply_modify'),
    url(r'^freeBoardprof_re_reply_write_ajax/$', views.freeBoardprof_re_reply_write_ajax, name='freeBoardprof_re_reply_write_ajax'),
    # 본문 수정을 위한 usercheck
    url(r'^freeBoardprof_usercheck/$', views.freeBoardprof_usercheck, name='freeBoardprof_usercheck'),

]
from django.conf.urls import include, url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # # 게시판 작성 시 6개 페이지 필요 : list / write (원글+답글) / delete / modify / detail
    url(r'^freeBoardprof_list/$', views.freeBoardprof_list, name='freeBoardprof_list'),
    url(r'^freeBoardprof_write/$', views.freeBoardprof_write, name='freeBoardprof_write'),
    # # # 답글을 의미한다.
    url(r'^freeBoardprof_write/(?P<freeBoardprof_pk>\d+)/$', views.freeBoardprof_write, name='freeBoardprof_write'),
    url(r'^freeBoardprof_delete/$', views.freeBoardprof_delete, name='freeBoardprof_delete'),
    url(r'^freeBoardprof_modify/$', views.freeBoardprof_modify, name='freeBoardprof_modify'),
    url(r'^freeBoardprof_detail/$', views.freeBoardprof_detail, name='freeBoardprof_detail'),
    url(r'^freeBoardprof_detail/(?P<freeBoardprof_pk>\d+)/$', views.freeBoardprof_detail, name='freeBoardprof_detail'),
    # freeBoardprof_thumb
    url(r'^ajax/freeBoardprof_thumb_ajax/$', views.freeBoardprof_thumb_ajax, name='freeBoardprof_thumb_ajax'),
    # freeBoardprof_reply
    url(r'^ajax/freeBoardprof_content_reply_write_ajax/$', views.freeBoardprof_content_reply_write_ajax, name='freeBoardprof_content_reply_write_ajax'),
    url(r'^freeBoardprof_reply_delete/$', views.freeBoardprof_reply_delete, name='freeBoardprof_reply_delete'),
    url(r'^freeBoardprof_reply_modify/$', views.freeBoardprof_reply_modify, name='freeBoardprof_reply_modify'),
    url(r'^freeBoardprof_re_reply_write_ajax/$', views.freeBoardprof_re_reply_write_ajax, name='freeBoardprof_re_reply_write_ajax'),
    # 본문 수정을 위한 usercheck
    url(r'^freeBoardprof_usercheck/$', views.freeBoardprof_usercheck, name='freeBoardprof_usercheck'),

]
