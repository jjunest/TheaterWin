# from django.conf.urls import include, url
from django.urls import include, path, re_path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 한국 주식 리스트
    path("stock_usa_list/", views.stock_usa_list, name="stock_usa_list"),
    path("stock_usa_detail/<str:stock_code>/", views.stock_usa_detail, name="stock_usa_detail"),

    # urls.py 예시
    path('get_stock_candle/<str:stock_code>/', views.get_stock_candle, name='get_stock_candle'),
    path('get_stock_candle_api/<str:stock_code>/', views.get_stock_candle_api, name='get_stock_candle_api'),

]
