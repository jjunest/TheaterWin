# fr    om django.conf.urls import include, url
from django.urls import include, path, re_path

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # path(r'^appchat/$', views.appchat, name='appchat'),
    # # editor wyswig
    # path(r'^tinymce/', include('tinymce.urls')),
    # path(r'^$', views.index, name='index'),
    # path(r'^index/$', views.index, name='index'),
    # path(r'^index_real/$', views.index_real, name='index_real'),
    # # url(r'^post/(?P<pk>\d+)/$', views.post_detail, name='post_detail'),
    # path(r'^signup/$', views.signup, name='signup'),
    # path(r'^winbook_list/$', views.winbook_list, name='winbook_list'),
    # path(r'^winbook_list/(?P<startdate>[\w\-]+)/(?P<enddate>[\w\-]+)/$', views.winbook_list, name='winbook_list'),
    # # # share picks
    # path(r'^/$', views.share_picks, name='share_picks'),
    # path(r'^winbook_insert/$', views.winbook_insert, name='winbook_insert'),
    # path(r'^to_winnerBros/$', views.to_winnerBros, name='to_winnerBros'),
    # path(r'^login_view/$', views.login_view, name='login_view'),
    # # url(r'^logout/$', auth_views.LogoutView.as_view(), {'next_page': '/'}),  # 로그아웃 후 홈으로 이동
    # path(r'^ajax/validate_username/$', views.validate_username, name='validate_username'),
    # path(r'^winbook_statistics/$', views.winbook_statistics, name='winbook_statistics'),
    # path(r'^winbook_calendar/$', views.winbook_calendar, name='winbook_calendar'),
    # path(r'^index_video_test/$', views.index_video_test, name='index_video_test'),
    # path(r'^list_delete/$', views.list_delete, name='list_delete'),
    # path(r'^list_usercheck/$', views.list_usercheck, name='list_usercheck'),
    # path(r'^winbook_modify/$', views.winbook_modify, name='winbook_modify'),
    # path(r'^error_404/$', views.error_404, name='error_404'),
    # path(r'^error_wronguser/$', views.error_wronguser, name='error_wronguser'),
    # path(r'^bower_test/$', views.bower_test, name='bower_test'),
    # path(r'^calendar_test/$', views.calendar_test, name='calendar_test'),
    # #
    # path(r'^kakaoapi_test/$', views.kakaoapi_test, name='kakaoapi_test'),
    # path(r'^ajax/winbook_statistics_ajax/$', views.winbook_statistics_ajax, name='winbook_statistics_ajax'),
    # path(r'^question_list/$', views.question_list, name='question_list'),
    # path(r'^question_write/$', views.question_write, name='question_write'),
    # # # 답글을 의미한다.
    # path(r'^question_write/(?P<question_pk>\d+)/$', views.question_write, name='question_write'),
    # # # 파라미터가 있는 url 은 2개가 동시에 필요하다. 기본 url + 파라미터 있는 url
    # # # url(r'^question_detail/$', views.question_detail, name='question_detail'),
    # path(r'^question_detail/(?P<question_pk>\d+)/$', views.question_detail, name='question_detail'),
    # path(r'^winbook_detail/(?P<record_pk>\d+)/$', views.winbook_detail, name='winbook_detail'),
    # path(r'^question_delete/$', views.question_delete, name='question_delete'),
    # path(r'^question_modify/$', views.question_modify, name='question_modify'),
    # path(r'^question_usercheck/$', views.question_usercheck, name='question_usercheck'),
    #
    # # 채팅룸
    # path(r'^full_chatting/$', views.full_chatting, name='full_chatting'),
    # path(r'^chatting_room/(?P<room_name>[^/]+)/$', views.chatting_room, name='chatting_room'),
    #
    # # question_thumb
    # path(r'^ajax/question_thumb_ajax/$', views.question_thumb_ajax, name='question_thumb_ajax'),
    # # question_reply
    # path(r'^ajax/content_reply_ajax/$', views.content_reply_ajax, name='content_reply_ajax'),
    # path(r'^question_reply_delete/$', views.question_reply_delete, name='question_reply_delete'),
    # path(r'^question_reply_modify/$', views.question_reply_modify, name='question_reply_modify'),
    # path(r'^question_re_reply_write_ajax/$', views.question_re_reply_write_ajax, name='question_re_reply_write_ajax'),
    #
    # # winbook_thumb
    # path(r'^ajax/winbook_thumb_ajax/$', views.winbook_thumb_ajax, name='winbook_thumb_ajax'),
    # # winbook_reply
    # path(r'^ajax/winbook_reply_ajax/$', views.winbook_reply_ajax, name='winbook_reply_ajax'),
    # path(r'^winbook_reply_delete/$', views.winbook_reply_delete, name='winbook_reply_delete'),
    # path(r'^winbook_reply_modify/$', views.winbook_reply_modify, name='winbook_reply_modify'),
    #
    # #stock_rank
    # path(r'^stock_rank/$', views.stock_rank, name='stock_rank'),
    # # stock_rank
    # path(r'^stock_rank_pop/(?P<rank_name>[^/]+)/(?P<market_sum_percent>\d+)/$', views.stock_rank_pop, name='stock_rank_pop'),
    # # url(r'^stock_rank_pop_marketsum/(?P<rank_name>[^/]+)/$', views.stock_rank_pop_marketsum, name='stock_rank_pop_marketsum'),
    # path(r'^stock_list_kospi/$', views.stock_list_kospi, name='stock_list_kospi'),
    # path(r'^stock_detail_kor/(?P<stock_code>\d+)/$', views.stock_detail_kor, name='stock_detail_kor'),
    # # url(r'^stock_rank_pop_marketsum/(?P<rank_name>[^/]+)/$', views.stock_rank_pop_marketsum, name='stock_rank_pop_marketsum'),
    #
    # path(r'^template_content_52/$', views.template_content_52, name='template_content_52'),

    # 기본 페이지 및 앱
    path("", views.index_real, name="index_real"),
    path("index_real/", views.index_real, name="index_real"),
    path("appchat/", views.appchat, name="appchat"),

    # WYSIWYG Editor
    path("tinymce/", include("tinymce.urls")),

    # 회원가입 및 로그인
    path("signup/", views.signup, name="signup"),
    path("login_view/", views.login_view, name="login_view"),

    # Winbook 관련
    path("winbook/list/", views.winbook_list, name="winbook_list"),
    path("winbook/list/<slug:startdate>/<slug:enddate>/", views.winbook_list, name="winbook_list"),
    path("winbook/insert/", views.winbook_insert, name="winbook_insert"),
    path("winbook/to_winnerBros/", views.to_winnerBros, name="to_winnerBros"),
    path("winbook/statistics/", views.winbook_statistics, name="winbook_statistics"),
    path("winbook/calendar/", views.winbook_calendar, name="winbook_calendar"),
    path("winbook/detail/<int:record_pk>/", views.winbook_detail, name="winbook_detail"),
    path("winbook/modify/", views.winbook_modify, name="winbook_modify"),
    path("winbook/delete/", views.list_delete, name="list_delete"),
    path("winbook/usercheck/", views.list_usercheck, name="list_usercheck"),

    path('/$', views.share_picks, name='share_picks'),


    # 주식 관련 URL
    path("stock_rank/", views.stock_rank, name="stock_rank"),
    path("stock_rank_pop/<slug:rank_name>/<int:market_sum_percent>/", views.stock_rank_pop, name="stock_rank_pop"),
    path("stock_list_kospi/", views.stock_list_kospi, name="stock_list_kospi"),
    path("stock_detail_kor/<int:stock_code>/", views.stock_detail_kor, name="stock_detail_kor"),

    # 게시판 (질문 관련)
    path("question/list/", views.question_list, name="question_list"),
    path("question/write/", views.question_write, name="question_write"),
    path("question/write/<int:question_pk>/", views.question_write, name="question_write"),
    path("question/detail/<int:question_pk>/", views.question_detail, name="question_detail"),
    path("question/delete/", views.question_delete, name="question_delete"),
    path("question/modify/", views.question_modify, name="question_modify"),
    path("question/usercheck/", views.question_usercheck, name="question_usercheck"),

    # 채팅 관련
    path("chatting/full/", views.full_chatting, name="full_chatting"),
    path("chatting/room/<slug:room_name>/", views.chatting_room, name="chatting_room"),

    # 에러 페이지
    path("error/404/", views.error_404, name="error_404"),
    path("error/wronguser/", views.error_wronguser, name="error_wronguser"),

    # 기타 페이지
    path("calendar_test/", views.calendar_test, name="calendar_test"),
    path("bower_test/", views.bower_test, name="bower_test"),
    path("index_video_test/", views.index_video_test, name="index_video_test"),

    # Ajax 관련 URL
    path("ajax/validate_username/", views.validate_username, name="validate_username"),
    path("ajax/winbook_statistics/", views.winbook_statistics_ajax, name="winbook_statistics_ajax"),
    path("ajax/winbook_thumb/", views.winbook_thumb_ajax, name="winbook_thumb_ajax"),
    path("ajax/winbook_reply/", views.winbook_reply_ajax, name="winbook_reply_ajax"),
    path("ajax/question_thumb/", views.question_thumb_ajax, name="question_thumb_ajax"),
    path("ajax/question_reply/", views.content_reply_ajax, name="content_reply_ajax"),
    path("ajax/winbook_re_reply/", views.question_re_reply_write_ajax, name="question_re_reply_write_ajax"),

    # 게시판 댓글 관련
    path("question/reply/delete/", views.question_reply_delete, name="question_reply_delete"),
    path("question/reply/modify/", views.question_reply_modify, name="question_reply_modify"),
    path("winbook/reply/delete/", views.winbook_reply_delete, name="winbook_reply_delete"),
    path("winbook/reply/modify/", views.winbook_reply_modify, name="winbook_reply_modify"),

    # 기타 URL
    path("template_content_52/", views.template_content_52, name="template_content_52"),
    path("base_template_250724/", views.base_template_250724, name="base_template_250724"),
    path("base_template_datatable_250724/", views.base_template_datatable_250724, name="base_template_datatable_250724"),

]
