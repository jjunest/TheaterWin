from django.conf.urls import include, url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # # 게시판 작성 시 6개 페이지 필요 : list / write (원글+답글) / delete / modify / detail
    url(r'^freeBoard_list/$', views.freeBoard_list, name='freeBoard_list'),
    url(r'^freeBoard_write/$', views.freeBoard_write, name='freeBoard_write'),
    # # # 답글을 의미한다.
    url(r'^freeBoard_write/(?P<freeBoard_pk>\d+)/$', views.freeBoard_write, name='freeBoard_write'),
    url(r'^freeBoard_delete/$', views.freeBoard_delete, name='freeBoard_delete'),
    url(r'^freeBoard_modify/$', views.freeBoard_modify, name='freeBoard_modify'),
    url(r'^freeBoard_detail/$', views.freeBoard_detail, name='freeBoard_detail'),
    url(r'^freeBoard_detail/(?P<freeBoard_pk>\d+)/$', views.freeBoard_detail, name='freeBoard_detail'),
    # freeBoard_thumb
    url(r'^ajax/freeBoard_thumb_ajax/$', views.freeBoard_thumb_ajax, name='freeBoard_thumb_ajax'),
    # freeBoard_reply
    url(r'^ajax/freeBoard_content_reply_write_ajax/$', views.freeBoard_content_reply_write_ajax, name='freeBoard_content_reply_write_ajax'),
    url(r'^freeBoard_reply_delete/$', views.freeBoard_reply_delete, name='freeBoard_reply_delete'),
    url(r'^freeBoard_reply_modify/$', views.freeBoard_reply_modify, name='freeBoard_reply_modify'),
    url(r'^freeBoard_re_reply_write_ajax/$', views.freeBoard_re_reply_write_ajax, name='freeBoard_re_reply_write_ajax'),
    # 본문 수정을 위한 usercheck
    url(r'^freeBoard_usercheck/$', views.freeBoard_usercheck, name='freeBoard_usercheck'),

]
