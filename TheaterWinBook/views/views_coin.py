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
from ..models_coins import CoinsUpbitList, CoinsUpbitCandle, CoinsUpbitTicker
from ..utils_coin import *
from django.shortcuts import render
from django.conf import settings
from ..utils_coin import *
from decimal import Decimal # Decimal 타입 임포트
from django.shortcuts import render, get_object_or_404
from django.utils import timezone # 🕒 시간대 처리 및 포매팅을 위해 추가
import locale
import platform
# 💡 Timezone 관련 문제 해결을 위해 TimeZone 객체를 가져옵니다.
from pytz import timezone as pytz_timezone


if platform.system() == "Windows":
    locale.setlocale(locale.LC_ALL, 'Korean')
else:
    # Linux/Mac 환경은 ko_KR.UTF-8을 사용하는 것이 일반적입니다.
    # 그러나 Django 템플릿 필터 사용이 더 간편할 수 있습니다.
    # 여기서는 포맷팅을 뷰에서 직접 처리하는 로직만 반영합니다.
    pass
# 한국 시간대 객체 정의 (settings.py의 TIME_ZONE이 'Asia/Seoul'일 경우)
KST = pytz_timezone('Asia/Seoul')


# 💡 재사용을 위해 Ticker 데이터 포맷팅 함수 정의
def format_ticker_data(latest_ticker):
    """최신 Ticker 데이터를 상세 페이지 표시용으로 포맷합니다."""
    if not latest_ticker:
        return None

    price_value = latest_ticker.ticker_trade_price

    # 1. 가격 포맷팅 및 소수점 처리
    display_price = '가격정보없음'
    if price_value is not None:
        decimal_places = get_price_display_format(price_value)
        formatted_price_with_comma = f"{price_value:,.{decimal_places}f}"
        display_price = formatted_price_with_comma

    # 2. 등락률 처리
    signed_change_rate = None
    if latest_ticker.ticker_signed_change_rate is not None:
        signed_change_rate = latest_ticker.ticker_signed_change_rate * Decimal(100)

    # 3. 시간 처리 (Naive Datetime 오류 방지 로직 재사용)
    bat_time = latest_ticker.bat_time
    formatted_bat_time = ''
    if bat_time:
        try:
            aware_bat_time = timezone.make_aware(bat_time, KST)
            bat_time_kst = timezone.localtime(aware_bat_time)
            formatted_bat_time = bat_time_kst.strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            formatted_bat_time = '시간 오류'

    return {
        # 최신 가격 요약
        'trade_price_display': display_price,
        'change_rate': signed_change_rate,
        'prev_closing_price': latest_ticker.ticker_prev_closing_price,
        'high_price': latest_ticker.ticker_high_price,
        'low_price': latest_ticker.ticker_low_price,

        # 시간 정보
        'updated_at_formatted': formatted_bat_time,

        # 원본 데이터 (필요한 경우)
        'ticker_data': latest_ticker,
    }



# 💡 코인별 포맷팅 자릿수 결정 함수
def get_price_display_format(price: Decimal):
    """가격의 크기에 따라 표시할 소수점 자릿수와 포맷팅을 결정합니다."""
    # KRW-BTC (수천만원 이상) -> 소수점 0~2자리
    if price >= Decimal(1000):
        return 0  # 1,000원 이상: 소수점 0자리 (원 단위만)
    # KRW-ETH (수백만원) -> 소수점 2~4자리
    elif price >= Decimal(100):
        return 2  # 100원 이상: 소수점 2자리
    # KRW-WAXP (수십원~수백원) -> 소수점 4자리
    elif price >= Decimal(1):
        return 4  # 1원 이상: 소수점 4자리
    # KRW-BTT (0.1원 미만) -> 소수점 6자리 (비트토렌트와 같은 극저가 코인)
    else:
        return 6  # 1원 미만: 소수점 6자리


def coin_list(request):
    """
    CoinsUpbitList와 CoinsUpbitTicker를 결합하여
    활성화된 코인의 이름, 티커, 최신 가격, 등락률, 업데이트 시각을 보여주는 뷰.
    """
    # ... (활성화된 코인 리스트 조회는 동일) ...
    active_coins = CoinsUpbitList.objects.filter(is_active=True).values(
        'coins_code',
        'coins_name_kor',
        'coins_name_eng'
    )
    coin_list_data = []

    for coin in active_coins:
        coin_code = coin['coins_code']

        latest_ticker = CoinsUpbitTicker.objects.filter(
            coins_code__coins_code=coin_code
        ).order_by('-bat_time').first()

        # 3. 데이터 통합 및 처리
        price_value = latest_ticker.ticker_trade_price if latest_ticker and latest_ticker.ticker_trade_price is not None else Decimal(
            -1)

        # (3), (4) 가격 포맷팅 및 소수점 처리
        display_price = '가격정보없음'
        if price_value != Decimal(-1) and price_value is not None:
            # 💡 소수점 자릿수 결정
            decimal_places = get_price_display_format(price_value)

            # 💡 천 단위 콤마 포맷팅 및 소수점 처리
            # Django 템플릿에서 humanize 필터를 사용하기 위해 포맷되지 않은 Decimal 그대로 전달
            # 템플릿에서 'intcomma' 필터를 사용하도록 변경합니다.
            display_price_raw = price_value

            # 💡 소수점 자릿수 정보를 템플릿에 전달
            formatted_price_with_comma = f"{price_value:,.{decimal_places}f}"
            display_price = formatted_price_with_comma

        # (3) 등락률: ticker_signed_change_rate를 100을 곱하여 퍼센트(%)로 변환
        if latest_ticker and latest_ticker.ticker_signed_change_rate is not None:
            signed_change_rate = latest_ticker.ticker_signed_change_rate * Decimal(100)
        else:
            signed_change_rate = None

        # (2) 현재가에 대한 시간 기준 처리 (Naive Datetime 오류 방지 로직 유지)
        bat_time = latest_ticker.bat_time if latest_ticker else None
        formatted_bat_time = ''
        bat_time_sort_value = 0

        if bat_time:
            try:
                # Naive Datetime 처리 유지
                aware_bat_time = timezone.make_aware(bat_time, KST)
                bat_time_kst = timezone.localtime(aware_bat_time)
                formatted_bat_time = bat_time_kst.strftime('%Y/%m/%d %H:%M:%S')
                bat_time_sort_value = bat_time_kst.timestamp()
            except Exception as e:
                print(f"Timezone Conversion Error: {e}")
                formatted_bat_time = '시간 오류'

        coin_list_data.append({
            'name_kor': coin['coins_name_kor'],
            'name_eng': coin['coins_name_eng'],
            'ticker': coin_code.split('-')[-1],
            'full_code': coin_code,
            'sort_price': price_value,
            # 💡 포맷팅된 문자열을 전달
            'latest_price_display': display_price,
            'signed_change_rate': signed_change_rate,
            'updated_at_formatted': formatted_bat_time,
            'updated_at_sort': bat_time_sort_value,
        })

    context = {
        'coin_list': coin_list_data,
        'title': '실시간 코인 가격 현황'
    }

    return render(request, 'TheaterWinBook/coin_list.html', context)


def coin_detail_view(request, coin_code):
    """
    특정 코인 코드(KRW-BTC)를 받아 상세 정보를 보여주는 뷰.
    """
    # 1. DB에서 해당 코인 정보 로드
    coin_list_info = get_object_or_404(CoinsUpbitList, coins_code=coin_code)

    # 2. 가장 최신 Ticker 데이터 로드 (선택 사항: 상세 정보 페이지에 활용)
    latest_ticker = CoinsUpbitTicker.objects.filter(
        coins_code__coins_code=coin_code
    ).order_by('-bat_time').first()

    context = {
        'coin_code': coin_code,
        'name_kor': coin_list_info.coins_name_kor,
        'ticker_data': latest_ticker,
        'page_title': f'{coin_list_info.coins_name_kor} 상세 분석',
        # ... 여기에 차트 데이터나 추가 정보를 로드하여 context에 포함 ...
    }
    return render(request, 'TheaterWinBook/coin_detail.html', context)




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
    # return render(request, 'TheaterWinBook/coin_list.html', {"coins": coins})

