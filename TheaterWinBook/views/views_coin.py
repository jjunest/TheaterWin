#this is django>view>views_coin.py
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

# 필요한 DB 모델을 import 합니다.
from ..models_coins import CoinsUpbitList, CoinsUpbitCandle
from ..utils_coin import *
from django.shortcuts import render
from django.conf import settings
from ..utils_coin import *




def coin_alarm(request):
    """코인 시세와 경보 정보를 웹 페이지에 표시하는 뷰"""

    # 1. DB에서 모든 코인 Ticker(coins_code)를 가져옵니다.
    db_coins = CoinsUpbitList.objects.all()
    # Ticker 목록만 추출하여 리스트로 만듭니다.
    db_tickers = [coin.coins_code for coin in db_coins]

    # 2. DB Ticker 목록을 get_coin_prices 함수에 전달하여 실시간 시세를 가져옵니다.
    realtime_prices = get_coin_prices(markets=db_tickers)

    # 3. DB 데이터와 실시간 시세 데이터를 결합합니다.
    # 딕셔너리로 변환하여 Ticker를 키(key)로 사용하면 데이터 결합이 용이합니다.
    realtime_price_dict = {price['market']: price for price in realtime_prices} if realtime_prices else {}
    print("this is realtime_price_dict",realtime_price_dict)
    combined_coins = []
    for db_coin in db_coins:
        # DB 데이터에 실시간 가격 정보 추가
        realtime_data = realtime_price_dict.get(db_coin.coins_code)
        if realtime_data:
            combined_data = {
                'name_kor': db_coin.coins_name_kor,
                'ticker': db_coin.coins_code,
                'warning': db_coin.warning,
                'price_fluctuations': db_coin.price_fluctuations,
                'trading_volume_soaring': db_coin.trading_volume_soaring,
                'deposit_amount_soaring': db_coin.deposit_amount_soaring,
                'global_price_differences': db_coin.global_price_differences,
                'concentration_of_small_accounts': db_coin.concentration_of_small_accounts,
                'trade_price': realtime_data.get('trade_price'),
                'signed_change_rate': realtime_data.get('signed_change_rate'),
            }
            combined_coins.append(combined_data)

    assets = get_upbit_assets(settings.UPBIT_ACCESS_KEY, settings.UPBIT_SECRET_KEY)

    context = {
        "coins": combined_coins,  # 결합된 데이터
        "assets": assets,
    }
    print("this is context:",context)
    return render(request, 'TheaterWinBook/coin_alarm.html', context)


def get_coin_candle(request, coin_code):
    """
    특정 코인의 캔들 데이터를 DB에서 조회하여 JSON 형식으로 반환하는 API
    """
    try:
        # coin_code에 해당하는 최신 캔들 데이터 100개를 가져옵니다.
        candles = CoinsUpbitCandle.objects.filter(coins_code__coins_code=coin_code).order_by(
            '-coin_candle_datetime_kst')[:100]
        # 🔑 중요: 쿼리 결과 개수와 내용을 확인
        print(f"✅ 쿼리 Ticker: {coin_code}")
        print(f"✅ DB 조회 건수: {len(candles)}")
        # 캔들 데이터를 JSON 직렬화가 가능한 리스트 형태로 변환합니다.
        # 이 형식은 ApexCharts의 캔들스틱 차트 데이터 형식과 호환됩니다.
        candle_data = [
            {
                'x': int(candle.coin_candle_datetime_kst.timestamp() * 1000),  # x축은 밀리초 단위의 Unix 타임스탬프
                'y': [
                    float(candle.coin_opening_price),
                    float(candle.coin_high_price),
                    float(candle.coin_low_price),
                    float(candle.coin_closing_price),
                ]
            }
            for candle in candles
        ]

        # 차트 출력을 위해 데이터를 오래된 순서부터 정렬합니다.
        candle_data.reverse()

        # 코인 한글 이름도 함께 전달하여 팝업 제목에 사용합니다.
        coin_name_kor = CoinsUpbitList.objects.get(coins_code=coin_code).coins_name_kor

        return JsonResponse({
            'status': 'success',
            'data': candle_data,
            'coin_name_kor': coin_name_kor
        })

    except CoinsUpbitList.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '코인을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)





def template_250705(request):
    return render(request, 'TheaterWinBook/template_content_250705.html')


def coin_chart_pop(request, coin_ticker):
    # ... (생략) ...
    # print("this is coin_char_pop_coin_ticker:",coin_ticker)
    # 1. DB에서 캔들 데이터 조회: 필드 이름 수정 반영
    try:
        candle_data = CoinsUpbitCandle.objects.filter(
            coins_code__coins_code=coin_ticker  # Foreign Key를 통한 필터링
        ).order_by('-coin_candle_datetime_kst')[:300].values(  # 최신 데이터 300개
            'coin_candle_datetime_utc',  # X축 시간
            'coin_opening_price',
            'coin_high_price',
            'coin_low_price',
            'coin_trade_price'  # 종가 (Close)
        )
        # 쿼리가 내림차순(최신순)이므로, 차트의 시간 순서에 맞게 다시 오름차순으로 뒤집습니다.
        # print("this is candle_data len:",len(candle_data))
        candle_data = list(reversed(list(candle_data)))
        # print("this is reverse candle_data_len:",len(candle_data))
    except Exception as e:
        print(f"DB 조회 오류: {e}")
        candle_data = []

    # 2. ApexCharts Candlestick 데이터 형식으로 변환 (필드명 수정 반영)
    ohlc_data = []
    line_data = []

    for candle in candle_data:
        # DB에서 조회한 필드 이름 사용: 'coin_candle_datetime_utc'
        timestamp_ms = int(candle['coin_candle_datetime_utc'].timestamp() * 1000)
        # print("this is candle[coin_opening_price]",candle['coin_opening_price'])
        # [Open, High, Low, Close] 순서 - DB 필드 이름 사용
        ohlc_data.append({
            'x': timestamp_ms,
            'y': [
                float(candle['coin_opening_price']),  # json을 위해 float() 변경
                float(candle['coin_high_price']),     # json을 위해 float() 변경
                float(candle['coin_low_price']),      # json을 위해 float() 변경
                float(candle['coin_trade_price'])     # json을 위해 float() 변경
            ]
        })

        # Line Series 데이터 - DB 필드 이름 사용
        line_data.append({
            'x': timestamp_ms,
            'y': float(candle['coin_trade_price'])
        })

    # print(f"this is ohlc_data: {ohlc_data}")
    # ... (나머지 JSON 및 context 설정은 동일) ...
    ohlc_json = json.dumps(ohlc_data)
    line_json = json.dumps(line_data)

    context = {
        'coin_ticker': coin_ticker,
        'page_title': f"{coin_ticker} 캔들 차트",
        'ohlc_data_json': ohlc_json,
        'line_data_json': line_json,
    }
    # print("this is coin_ticker:",coin_ticker)
    # print("this is ohlc_Data_json:",ohlc_json)
    # print("this is line_Data_json:",line_json)

    return render(request, 'TheaterWinBook/coin_chart_pop.html', context)

# def coin_prices_view(request):
    # return render(request, 'TheaterWinBook/coin_alarm.html', {"coins": coins})

