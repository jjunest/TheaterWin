# from django.conf.urls import include, url
from django.urls import include, path, re_path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 한국 주식 리스트
    path("stock_korea_list/", views.stock_korea_list, name="stock_korea_list"),
    path("stock_korea_detail/<str:stock_code>/", views.stock_korea_detail, name="stock_korea_detail"),

    # urls.py 예시
    path('get_stock_candle/<str:stock_code>/', views.get_stock_candle, name='get_stock_candle'),
    path('get_stock_candle_api/<str:stock_code>/', views.get_stock_candle_api, name='get_stock_candle_api'),

]
