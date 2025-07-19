
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect


from ..forms import freeBoardForm, freeBoardForm
from ..models_freeboard import FreeBoard, FreeBoardInfo, FreeBoardReply
from django.contrib import messages
from django.db.models import F
from django.db.models import Max, Min
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page
import traceback
from django.shortcuts import render
from django.utils.safestring import mark_safe
import json

from django.shortcuts import render
from django.conf import settings
from ..utils_coin import *




def coin_alarm(request):
    """코인 시세를 웹 페이지에 표시하는 뷰"""
    coins = get_coin_prices()
    print("this is coins:",str(coins))

    assets = get_upbit_assets(settings.UPBIT_ACCESS_KEY, settings.UPBIT_SECRET_KEY)
    print ("this is assets:",assets)

    # race chart 그리기 예시 데이터
    data_by_time = [
        {"time": "2020", "data": [{"x": 1, "y": 10}, {"x": 2, "y": 20}, {"x": 3, "y": 30}]},
        {"time": "2021", "data": [{"x": 1, "y": 15}, {"x": 2, "y": 35}, {"x": 3, "y": 40}]},
        {"time": "2022", "data": [{"x": 1, "y": 20}, {"x": 2, "y": 25}, {"x": 3, "y": 45}]}
    ]


    return render(request, 'TheaterWinBook/coin_alarm.html', {"coins": coins, 'assets': assets, 'data_by_time':data_by_time})

def template_250705(request):


    return render(request, 'TheaterWinBook/template_content_250705.html')




# def coin_prices_view(request):
    # return render(request, 'TheaterWinBook/coin_alarm.html', {"coins": coins})

