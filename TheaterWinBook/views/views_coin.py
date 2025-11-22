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
from datetime import date, timedelta
import pandas as pd


if platform.system() == "Windows":
    locale.setlocale(locale.LC_ALL, 'Korean')
else:
    # Linux/Mac 환경은 ko_KR.UTF-8을 사용하는 것이 일반적입니다.
    # 그러나 Django 템플릿 필터 사용이 더 간편할 수 있습니다.
    # 여기서는 포맷팅을 뷰에서 직접 처리하는 로직만 반영합니다.
    pass
# 한국 시간대 객체 정의 (settings.py의 TIME_ZONE이 'Asia/Seoul'일 경우)
KST = pytz_timezone('Asia/Seoul')


def calculate_all_coin_mdd_rank(target_coin_code, days):
    """
    특정 기간(days) 동안의 전체 코인에 대한 MDD를 계산하고
    대상 코인의 순위 및 백분율을 반환합니다.
    """
    all_coins = CoinsUpbitList.objects.all()
    all_mdd_results = []
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # 1. 모든 코인에 대해 MDD 계산 및 데이터 수집
    for coin in all_coins:
        # 해당 기간의 캔들 데이터 조회 (종가/coin_trade_price 기준)
        prices_queryset = CoinsUpbitCandle.objects.filter(
            coins_code__coins_code=coin.coins_code,  # 조회 최적화를 위해 코드로 필터링
            coin_candle_datetime_kst__date__range=[start_date, end_date]
        ).order_by('coin_candle_datetime_kst').values('coin_trade_price')

        if prices_queryset.exists():
            prices_data_list = [
                {'trade_price': float(p['coin_trade_price'])}
                for p in prices_queryset
                if p['coin_trade_price'] is not None
            ]

            if prices_data_list:
                prices_df = pd.DataFrame(prices_data_list)
                latest_price = prices_df['trade_price'].iloc[-1]

                # calculate_mdd 함수 호출 (Peak Price는 필요 없으므로 _로 처리)
                _, _, mdd_percentage = calculate_mdd(prices_df, latest_price)

                all_mdd_results.append({
                    'code': coin.coins_code,
                    'mdd_percent': Decimal(str(mdd_percentage)),  # Decimal로 저장
                })

    # 2. MDD 기준 오름차순 정렬 (MDD 값이 작을수록 = 낙폭이 적을수록 순위가 높음)
    sorted_mdd = sorted(all_mdd_results, key=lambda x: x['mdd_percent'])

    # 3. 대상 코인의 순위 및 백분율 계산
    total_count = len(sorted_mdd)
    target_rank = 0

    for i, result in enumerate(sorted_mdd):
        if result['code'] == target_coin_code:
            target_rank = i + 1
            break

    rank_percentage = (target_rank / total_count) * 100 if total_count > 0 else Decimal('0.0')

    return {
        'total_count': total_count,
        'rank': target_rank,
        'rank_percent': Decimal(str(rank_percentage)),  # 백분율을 Decimal로
    }

def calculate_mdd(prices_df, current_price, days=180):
    """
    주어진 기간(days) 내 최고가 대비 현재 가격의 MDD(Maximum Drawdown)를 계산합니다.
    prices_df: 해당 기간의 가격 데이터프레임 (예: ['trade_price'] 컬럼 포함)
    current_price: 가장 최근의 현재 가격
    """
    if prices_df.empty:
        return None, None, 0.0, 0.0

    # 1. 해당 기간 내 최고가 (Peak Price) 계산
    peak_price = prices_df['trade_price'].max()
    # 계산을 위해 float 타입을 decimal 타입으로 변경
    peak_price_decimal = Decimal(str(peak_price))
    print("this is peak_price:",peak_price)
    print("this is current_price:",current_price)

    # 2. 현재 MDD 계산
    # (최고가 - 현재가) / 최고가 * 100

    # 나눗셈 시 ZeroDivisionError 방지를 위해 체크
    if peak_price_decimal == Decimal('0'):
        mdd_percentage = Decimal('0')
    else:
        # (Decimal - Decimal) / Decimal * Decimal 연산으로 안전하게 수행
        mdd_percentage = ((peak_price_decimal - current_price) / peak_price_decimal) * Decimal('100')
    print("this is mdd_percentage:",mdd_percentage)
    # 3. 데이터프레임을 이용한 실제 MDD 계산 (참고용, 사용자에게는 현재 MDD를 보여줌)
    # cum_max = prices_df['trade_price'].cummax()
    # drawdowns = (prices_df['trade_price'] - cum_max) / cum_max
    # max_drawdown_actual = drawdowns.min() * 100 # 전체 기간 중 최대 낙폭

    return peak_price, current_price, mdd_percentage


# 💡 재사용을 위해 Ticker 데이터 포맷팅 함수를 Candle 데이터 포맷팅 함수로 변경/정의
def format_candle_data(latest_candle, latest_ticker_for_rate):
    """
    최신 Candle 데이터를 상세 페이지 표시용으로 포맷하고,
    실시간 등락률을 위해 Ticker 데이터를 병합합니다.
    """
    if not latest_candle:
        return None

    # ⭐️ Candle의 종가(trade_price)를 현재가로 사용
    price_value = latest_candle.coin_trade_price

    # 1. 가격 포맷팅 및 소수점 처리
    display_price = '가격정보없음'
    if price_value is not None:
        decimal_places = get_price_display_format(price_value)
        formatted_price_with_comma = f"{price_value:,.{decimal_places}f}"
        display_price = formatted_price_with_comma

    # 2. 등락률 처리 (Candle에는 등락률 필드가 없으므로, Ticker에서 가져옵니다.)
    signed_change_rate = None
    if latest_ticker_for_rate and latest_ticker_for_rate.ticker_signed_change_rate is not None:
        signed_change_rate = latest_ticker_for_rate.ticker_signed_change_rate * Decimal(100)

    # 3. 시간 처리 (Candle의 시간 사용)
    bat_time = latest_candle.coin_candle_datetime_kst
    formatted_bat_time = ''
    if bat_time:
        try:
            # Candle 시간 필드는 보통 이미 Timezone-aware이거나, 최소한 KST 기준이므로
            # Naive/Aware 처리 로직을 조정합니다. (기존 로직 유지)
            aware_bat_time = timezone.make_aware(bat_time, KST)
            bat_time_kst = timezone.localtime(aware_bat_time)
            formatted_bat_time = bat_time_kst.strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            formatted_bat_time = '시간 오류'

    return {
        # ⭐️ 최신 가격 요약 (Candle 기반)
        'trade_price_display': display_price,
        'change_rate': signed_change_rate,  # Ticker 기반
        # ⭐️ Candle의 가격 정보 사용
        'prev_closing_price': latest_candle.coin_opening_price,  # 캔들에서는 시가(Open)를 전일 종가처럼 임시 사용하거나, 별도 필드 활용
        'high_price': latest_candle.coin_high_price,
        'low_price': latest_candle.coin_low_price,

        # 시간 정보 (Candle 기반)
        'updated_at_formatted': formatted_bat_time,

        # ⭐️ 원본 데이터 (필요한 경우)
        'candle_data': latest_candle,
    }



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

        latest_candle = CoinsUpbitCandle.objects.filter(
            coins_code__coins_code=coin_code
        ).order_by('-coin_candle_datetime_kst').first()

        # 가격: coin_trade_price (종가)
        price_value = latest_candle.coin_trade_price if latest_candle and latest_candle.coin_trade_price is not None else Decimal(
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

        # ⭐️ 등락률을 위해 Ticker를 다시 가져오는 로직 추가 (Candle의 시간/가격은 유지)
        latest_ticker_for_change_rate = CoinsUpbitTicker.objects.filter(
            coins_code__coins_code=coin_code
        ).order_by('-bat_time').first()

        if latest_ticker_for_change_rate and latest_ticker_for_change_rate.ticker_signed_change_rate is not None:
            signed_change_rate = latest_ticker_for_change_rate.ticker_signed_change_rate * Decimal(100)
        else:
            signed_change_rate = None

        # (2) 현재가에 대한 시간 기준 처리 (Naive Datetime 오류 방지 로직 유지)
        bat_time = latest_candle.coin_candle_datetime_kst if latest_candle else None
        formatted_bat_time = ''
        bat_time_sort_value = 0

        if bat_time:
            try:
                # Candle 시간은 이미 KST로 저장되어 있을 가능성이 높지만, Timezone 처리는 유지
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
            # ⭐️ 등락률은 Ticker에서 가져온 값 사용
            'signed_change_rate': signed_change_rate,
            # ⭐️ Candle의 기준 시간 사용
            'updated_at_formatted': formatted_bat_time,
            # ⭐️ Candle의 기준 시간 정렬 값 사용
            'updated_at_sort': bat_time_sort_value,
        })

    context = {
        'coin_list': coin_list_data,
        'title': '실시간 코인 가격 현황'
    }

    return render(request, 'TheaterWinBook/coin_list.html', context)


def coin_detail_view(request, coin_code):
    print("this is coin_view_detail")
    # 1. DB에서 해당 코인 정보 로드
    coin_list_info = get_object_or_404(CoinsUpbitList, coins_code=coin_code)

    # ⭐️ 변경: Ticker 대신 최신 Candle 데이터 로드 (MDD의 기준 가격이 됩니다)
    latest_candle = CoinsUpbitCandle.objects.filter(
        coins_code__coins_code=coin_code
    ).order_by('-coin_candle_datetime_kst').first()

    # ⭐️ 추가: 등락률 계산을 위해 최신 Ticker 데이터도 로드 (Ticker의 실시간 등락률을 사용합니다)
    latest_ticker_for_rate = CoinsUpbitTicker.objects.filter(
        coins_code__coins_code=coin_code
    ).order_by('-bat_time').first()

    # ⭐️ 변경: Candle 데이터를 기반으로 요약 데이터 포맷팅
    ticker_summary = format_candle_data(latest_candle, latest_ticker_for_rate)

    # ⭐️ Candle의 종가(coin_trade_price)를 현재 MDD 계산의 기준 가격으로 사용
    current_price = latest_candle.coin_trade_price if latest_candle else None
    print("this is current_price (from Candle):", current_price)
    # 2. 기간 설정 및 MDD 계산
    time_periods = {
        '1m': 30,  # 3개월 (약 90일)
        '3m': 90,  # 3개월 (약 90일)
        '6m': 180,  # 6개월 (약 180일)
        '12m': 365,  # 12개월 (약 365일)
        '18m': 548,  # 18개월 (약 548일)
    }

    mdd_results = {}

    if current_price:
        end_date = timezone.now().date()

        for key, days in time_periods.items():
            start_date = end_date - timedelta(days=days)
            print("this is end_date:", end_date)
            print("this is start_date:",start_date)

            # 해당 기간의 캔들 데이터 조회 (종가/coin_trade_price 기준) (이하 동일)
            prices_queryset = CoinsUpbitCandle.objects.filter(
                coins_code__coins_code=coin_code,
                coin_candle_datetime_kst__date__range=[start_date, end_date]
            ).order_by('coin_candle_datetime_kst').values('coin_trade_price')

            peak_price = None
            mdd_percentage = 0.0

            if prices_queryset.exists():
                prices_data_list = [
                    {'trade_price': float(p['coin_trade_price'])}
                    for p in prices_queryset
                    if p['coin_trade_price'] is not None
                ]

                if prices_data_list:
                    prices_df = pd.DataFrame(prices_data_list)
                    print("this is price_df:",prices_df)

                    # MDD 계산 함수 호출
                    peak_price, _, mdd_percentage = calculate_mdd(prices_df, current_price)
                    print("this is peak_price:",peak_price)
                    print("this is mdd_percentage:",mdd_percentage)

                    # 💡 Peak Price 포맷팅 (쉼표 및 소수점 0자리)
                    peak_price_formatted = f"{Decimal(peak_price):,.0f}" if peak_price is not None else 'N/A'
                    print("this is peak_price_formatted:",peak_price_formatted)
                    # 💡 MDD 순위 (임시 값)
                    # 💡 수정 코드: 모든 상수(25.5, 0.1)를 Decimal 타입으로 변환
                    # 4. 기준 기간 MDD 순위 계산 및 결과에 추가
                    # 💡 기간별 MDD 순위 계산 및 반영 (추가된 핵심 로직)
                    try:
                        mdd_rank_info = calculate_all_coin_mdd_rank(coin_code, days)
                        mdd_rank = mdd_rank_info['rank']
                        mdd_total = mdd_rank_info['total_count']
                        mdd_rank_percent = mdd_rank_info['rank_percent']  # Decimal 타입
                    except Exception as e:
                        print(f"기간 {key} MDD 순위 계산 오류: {e}")
                        mdd_rank = 'N/A'
                        mdd_total = 'N/A'
                        mdd_rank_percent = Decimal('0.0')

                    mdd_results[key] = {
                        'label': f"{days}일",
                        'peak_price': peak_price_formatted,
                        'current_price': current_price,
                        'mdd_percent': mdd_percentage,
                        # 💡 순위 정보를 mdd_results에 추가
                        'mdd_rank': mdd_rank,
                        'mdd_total_count': mdd_total,
                        'mdd_rank_percent': mdd_rank_percent,
                    }
                    print("mdd_rank:",mdd_rank)
                else:
                    mdd_results[key] = {'label': f"{days}일", 'peak_price': '데이터 부족', 'mdd_percent': 0.0,
                                        'mdd_rank': 'N/A', 'mdd_total_count': 'N/A', 'mdd_rank_percent': Decimal('0.0')}

            else:
                mdd_results[key] = {'label': f"{days}일", 'peak_price': '데이터 없음', 'mdd_percent': 0.0,
                                    'mdd_rank': 'N/A', 'mdd_total_count': 'N/A', 'mdd_rank_percent': Decimal('0.0')}

    context = {
        'coin_code': coin_code,
        'ticker': coin_code.split('-')[-1],
        'name_kor': coin_list_info.coins_name_kor,
        'name_eng': coin_list_info.coins_name_eng,
        # ⭐️ latest_ticker 대신 latest_candle 원본 객체 전달 (필요시 사용)
        'latest_candle': latest_candle,
        # ⭐️ Candle 기반의 요약 데이터 전달
        'ticker_summary': ticker_summary,
        'page_title': f'{coin_list_info.coins_name_kor} 상세 분석',
        'mdd_results': mdd_results,  # 💡 기간별 MDD 결과 데이터 추가
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

