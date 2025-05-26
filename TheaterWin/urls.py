"""TheaterWin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
# from django.conf.urls import include, url
from django.urls import include, path, re_path
from django.contrib import admin

from TheaterWinBook import views  # Import your app views


from django.urls import path
# from . import views  # Import your views

urlpatterns = [

    path('', views.index, name='index'),  # Make sure this exists
    # path('index/', views.index, name='index'),  # Alternative route for testing
    path('admin/', admin.site.urls),
    # 앱 별로 개별 URLConf를 포함하도록 수정
    path("", include("TheaterWinBook.urls")),
    path("", include("TheaterWinBook.urls_freeboard")),
    path("", include("TheaterWinBook.urls_freeboardstock")),
    path("", include("TheaterWinBook.urls_freeboardprof")),
    path("", include("TheaterWinBook.urls_coin")),
    # Django 인증 URL 포함
    path("accounts/", include("django.contrib.auth.urls")),

    # 기타 URL
    path("template_content_52/", views.template_content_52, name="template_content_52"),

]
