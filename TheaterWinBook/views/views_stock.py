import time

import datetime
import pandas as pd
import pytz
from datetime import timedelta  # <--- 이렇게 수정해야 합니다.
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.encoding import smart_str
# from django.utils.encoding import smart_text

from ..forms import UserForm, LoginForm, TheaterWinBookRecordForm, TheaterWinQuestionForm
from ..models import Post, TheaterWinBookRecord, TheaterWinQuestion, TheaterWinQuestionInfo, TheaterWinQuestionReply, Full_Chatting_Message, TheaterWinBookRecordInfo, TheaterWinBookRecordReply, StockSummaryKr, StockList
from django.contrib import messages
from django.contrib.messages import get_messages
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F
from django.db.models import Max, Min
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page
import traceback
from django.shortcuts import render
from django.utils.safestring import mark_safe
import json
# 실제 정의하신 모델 임포트
from ..models_stock_korea import StocksKrList, StocksKrCandle, StocksKrTicker
from decimal import Decimal
from ..models_stock_usa import StocksUsList, StocksUsTicker, StocksUsCandle # 모델명 확인

# stock_rank
def stock_rank(request):
    return render(request, 'TheaterWinBook/stock_rank.html')


# stock_rank
def stock_rank_korea(request):
    return render(request, 'TheaterWinBook/stock_rank_korea.html')


def stock_rank_pop(request, rank_name, market_sum_percent):
    print("this is ranktype:", rank_name)
    latest_date = StockSummaryKr.objects.filter().latest('info_date')
    print("this is lastest_date:", latest_date.info_date)
    # latest_date_list = list(latest_date)
    # print("this is latest_date_list", latest_date_list)
    latest_date = StockSummaryKr.objects.filter().latest('info_date')


    # Global Condition (like market_sum_percentage)
    print("this is market_sum_percent:", market_sum_percent)
    market_sum_percent = int(market_sum_percent)
    total_rows = StockSummaryKr.objects.count()
    print ("this is total_rows:", str(total_rows))
    num_rows = int(total_rows * market_sum_percent / 100)
    print ("this is num_rows:" , str(num_rows))

    StockSummaryKr_MarketSumCondition = StockSummaryKr.objects.raw("SELECT * FROM TheaterWinBook_stocksummarykr "
                                       "WHERE info_date = (SELECT info_date FROM TheaterWinBook_stocksummarykr "
                                       "ORDER BY info_date DESC LIMIT 1) ORDER BY STOCK_MARKET_SUM DESC LIMIT %s", [num_rows])
    print("this is num_rows(tobe) ", str(len(list(StockSummaryKr_MarketSumCondition))))

    # rank name 에 따라 top stock 10 개 리스트를 추려서 화면에 뿌려줌
    if rank_name == "marketsum":
        top_stock = StockSummaryKr.objects.raw("SELECT * FROM TheaterWinBook_stocksummarykr "
                                            "WHERE info_date = (SELECT info_date FROM TheaterWinBook_stocksummarykr "
                                            "ORDER BY info_date DESC LIMIT 1) "
                                            "AND 1=1 "
                                            "ORDER BY STOCK_MARKET_SUM DESC LIMIT 10")

    # rank name(per_desc) 에 따라 top stock 10 개 리스트를 추려서 화면에 뿌려줌
    if rank_name == "per_desc":
        top_stock = StockSummaryKr.objects.raw("SELECT * FROM TheaterWinBook_stocksummarykr "
                                            "WHERE info_date = (SELECT info_date FROM TheaterWinBook_stocksummarykr "
                                            "ORDER BY info_date DESC LIMIT 1) "
                                            "AND 1=1 "
                                            "AND typeof(stock_per) = 'real'"
                                            "ORDER BY stock_per DESC LIMIT 10")

    for p in top_stock :
        print("%s 번째, %s" % (p.stock_name,p))
    top_stock_list = list(top_stock)

    return render(request, 'TheaterWinBook/stock_rank_pop.html',{"top_stock": top_stock})
    # return render(request, 'TheaterWinBook/stock_rank_pop.html',{"top10": top10_result})


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import pandas as pd
import pytz
from ..models_stock_korea import StocksKrList, StocksKrTicker, StocksKrCandle

KST = pytz.timezone('Asia/Seoul')


def stock_korea_detail(request, stock_code):
    """한국 주식 상세 분석 뷰 (Ticker 및 MDD 분석)"""
    stock_info = get_object_or_404(StocksKrList, stock_code=stock_code)

    # 1. 실시간 Ticker 및 최신 Candle 데이터 로드
    latest_ticker = StocksKrTicker.objects.filter(stock_code=stock_info).order_by('-bat_time').first()
    latest_candle = StocksKrCandle.objects.filter(stock_code=stock_info).order_by('-date').first()

    # 2. 현재가 결정 (Ticker 우선)
    current_price = Decimal('0')
    if latest_ticker:
        current_price = latest_ticker.ticker_close_price
    elif latest_candle:
        current_price = latest_candle.close_price

    # 3. 요약 정보 포맷팅 (주식은 원단위이므로 int처리)
    summary = {
        'price_display': f"{int(current_price):,}" if current_price > 0 else "가격정보없음",
        'change_rate': (
                    latest_ticker.ticker_change_rate * 100) if latest_ticker and latest_ticker.ticker_change_rate else 0,
        'high_price': f"{int(latest_ticker.ticker_high_price or 0):,}" if latest_ticker else "-",
        'low_price': f"{int(latest_ticker.ticker_low_price or 0):,}" if latest_ticker else "-",
        'prev_close': f"{int(latest_ticker.ticker_prev_close or 0):,}" if latest_ticker else "-",
        'updated_at': latest_ticker.bat_time.astimezone(KST).strftime('%Y/%m/%d %H:%M:%S') if latest_ticker else "-"
    }

    # 4. MDD 퀀트 분석 (코인 로직 이식)
    time_periods = {'1m': 30, '3m': 90, '6m': 180, '12m': 365}
    mdd_results = {}
    end_date = timezone.now().date()

    if current_price > 0:
        for key, days in time_periods.items():
            start_date = end_date - timedelta(days=days)
            prices_qs = StocksKrCandle.objects.filter(
                stock_code=stock_info,
                date__range=[start_date, end_date]
            ).order_by('date').values('close_price')

            if prices_qs.exists():
                df = pd.DataFrame(list(prices_qs))
                peak_price = float(df['close_price'].max())
                # MDD 계산: (현재가 - 최고가) / 최고가 * 100
                mdd_val = ((float(current_price) - peak_price) / peak_price) * 100 if peak_price > 0 else 0

                mdd_results[key] = {
                    'label': f"{days}일",
                    'peak_price': f"{int(peak_price):,}",
                    'current_price': f"{int(current_price):,}",
                    'mdd_percent': Decimal(str(mdd_val)),
                    'mdd_rank_percent': abs(round(mdd_val, 1))  # 임시 리스크 점수
                }

    context = {
        'stock_info': stock_info,
        'stock_code': stock_code,
        'summary': summary,
        'latest_ticker': latest_ticker,
        'mdd_results': mdd_results,
        'page_title': f"{stock_info.stock_name} 상세 분석",
    }
    return render(request, 'TheaterWinBook/stock_korea_detail.html', context)


def stock_usa_detail(request, stock_code):
    """
    미국 주식 상세 분석 뷰
    """
    # 1. 기본 종목 정보 로드 (상단에서 전달받은 stock_code 사용)
    stock_info = get_object_or_404(StocksUsList, symbol=stock_code.upper())

    # 2. 데이터 로드 (Ticker 우선, Candle 백업)
    latest_ticker = StocksUsTicker.objects.filter(symbol=stock_info).order_by('-bat_time').first()
    latest_candle = StocksUsCandle.objects.filter(symbol=stock_info).order_by('-date').first()

    # 3. 기준 현재가 결정
    current_price = Decimal('0')
    display_date = "-"

    if latest_ticker:
        current_price = latest_ticker.price
        display_date = latest_ticker.bat_time.astimezone(KST).strftime('%Y/%m/%d %H:%M:%S')
    elif latest_candle:
        current_price = latest_candle.close_price
        display_date = latest_candle.date.strftime('%Y/%m/%d') + " (종가)"

    # 4. 요약 정보 (미국 주식은 소수점 2자리 필수)
    summary = {
        'price_display': f"{float(current_price):,.2f}" if current_price > 0 else "0.00",
        'change_rate': (latest_ticker.change_rate * 100) if latest_ticker and latest_ticker.change_rate else 0,
        'high': f"{float(latest_ticker.high or 0):,.2f}" if latest_ticker else "-",
        'low': f"{float(latest_ticker.low or 0):,.2f}" if latest_ticker else "-",
        'open': f"{float(latest_ticker.open or 0):,.2f}" if latest_ticker else "-",
        'updated_at': display_date,
    }

    # 5. MDD 분석 (기존 로직 유지)
    time_periods = {'1m': 30, '3m': 90, '6m': 180, '12m': 365}
    mdd_results = {}
    analysis_end_date = latest_candle.date if latest_candle else timezone.now().date()

    if current_price > 0:
        for key, days in time_periods.items():
            start_date = analysis_end_date - timedelta(days=days)
            prices_qs = StocksUsCandle.objects.filter(
                symbol=stock_info,
                date__range=[start_date, analysis_end_date]
            ).order_by('date').values('high_price', 'close_price')

            if prices_qs.exists():
                df = pd.DataFrame(list(prices_qs))
                peak_price = float(df['high_price'].max())
                mdd_val = ((float(current_price) - peak_price) / peak_price) * 100 if peak_price > 0 else 0

                mdd_results[key] = {
                    'label': f"{days}일",
                    'peak_price': f"{peak_price:,.2f}",
                    'current_price': f"{float(current_price):,.2f}",
                    'mdd_percent': mdd_val,
                    'risk_score': abs(round(mdd_val, 1))
                }

    context = {
        'stock_info': stock_info,
        'stock_code': stock_code.upper(),  # symbol 대신 stock_code로 통일하여 NameError 해결
        'summary': summary,
        'latest_ticker': latest_ticker,
        'mdd_results': mdd_results,
    }
    return render(request, 'TheaterWinBook/stock_usa_detail.html', context)

def format_us_market_cap(value):
    """미국 시가총액 단위 변환 헬퍼 함수"""
    if not value: return "-"
    val = float(value)
    if val >= 1_000_000_000_000:
        return f"${val / 1_000_000_000_000:.2f}T (조)"
    elif val >= 1_000_000_000:
        return f"${val / 1_000_000_000:.2f}B (십억)"
    return f"${val / 1_000_000:.2f}M (백만)"


def get_us_stock_candle_api(request, symbol):
    """미국 주식 ApexCharts용 API"""
    candles = StocksUsCandle.objects.filter(symbol__symbol=symbol.upper()).order_by('-date')[:250]
    data = [{
        'x': int(timezone.datetime.combine(c.date, timezone.datetime.min.time()).timestamp() * 1000),
        'y': [float(c.open_price), float(c.high_price), float(c.low_price), float(c.close_price)]
    } for c in reversed(candles)]

    return JsonResponse({'status': 'success', 'data': data})




def get_stock_candle(request, stock_code):
    """주식 캔들 데이터 API (ApexCharts용)"""
    try:
        # 최근 200봉 조회
        candles = StocksKrCandle.objects.filter(stock_code__stock_code=stock_code).order_by('-date')[:200]
        candle_data = [
            {
                'x': int(timezone.datetime.combine(c.date, timezone.datetime.min.time()).timestamp() * 1000),
                'y': [float(c.open_price), float(c.high_price), float(c.low_price), float(c.close_price)]
            }
            for c in reversed(candles)
        ]
        stock_name = StocksKrList.objects.get(stock_code=stock_code).stock_name
        return JsonResponse({'status': 'success', 'data': candle_data, 'stock_name': stock_name})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def val_label(days):
    if days >= 30: return f"{days // 30}개월"
    return f"{days}일"


# # 캔들 차트 API (ApexCharts용)
# def get_stock_candle_api(request, stock_code):
#     candles = StocksKrCandle.objects.filter(stock_code__stock_code=stock_code).order_by('-date')[:300]
#     data = [{
#         'x': int(time.mktime(c.date.timetuple()) * 1000),
#         'y': [float(c.open_price), float(c.high_price), float(c.low_price), float(c.close_price)]
#     } for c in reversed(candles)]
#
#     return JsonResponse({'status': 'success', 'data': data, 'name': '주가 차트'})

# # 캔들 차트 API (ApexCharts용)
def get_stock_candle_api(request, stock_code):
    """
    시장 구분(KR/US)을 자동 감지하여 캔들 데이터를 반환하는 통합 API
    """
    # 1. 시장 구분 로직 (간단하게 알파벳 포함 여부로 US 주식 판단)
    # 혹은 요청에 ?market=US 같은 파라미터를 명시적으로 받을 수도 있습니다.
    is_us_stock = any(c.isalpha() for c in stock_code)

    try:
        if is_us_stock:
            # 미국 주식 처리 (StocksUsCandle 사용)
            # StocksUsCandle은 ForeignKey(symbol) 구조이므로 symbol__symbol로 필터링
            candles = StocksUsCandle.objects.filter(symbol__symbol=stock_code).order_by('-date')[:300]
            chart_name = f"{stock_code} (US) Chart"
        else:
            # 한국 주식 처리 (StocksKrCandle 사용)
            candles = StocksKrCandle.objects.filter(stock_code__stock_code=stock_code).order_by('-date')[:300]
            chart_name = "국내 주가 차트"

        if not candles.exists():
            return JsonResponse({'status': 'error', 'message': 'No data found'}, status=404)

        # 2. ApexCharts 데이터 포맷팅 (통일)
        data = [{
            'x': int(time.mktime(c.date.timetuple()) * 1000),
            'y': [
                float(c.open_price),
                float(c.high_price),
                float(c.low_price),
                float(c.close_price)
            ]
        } for c in reversed(candles)]

        return JsonResponse({
            'status': 'success',
            'market': 'US' if is_us_stock else 'KR',
            'data': data,
            'name': chart_name
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def stock_usa_list(request):
    """
        미국 주식 리스트 뷰 (NASDAQ, NYSE, AMEX)
        한국 주식 로직을 계승하되, 달러($) 및 소수점 처리를 추가함.
        """
    # 1. 활성화된 미국 주식 리스트 조회
    active_stocks = StocksUsList.objects.filter(is_active=True).values(
        'symbol', 'name_en', 'name_ko', 'market', 'sector', 'industry'
    )

    stock_list_data = []

    for stock in active_stocks:
        symbol = stock['symbol']

        # 최신 티커 데이터 조회 (StocksUsTicker 모델 기준)
        latest_ticker = StocksUsTicker.objects.filter(
            symbol__symbol=symbol
        ).order_by('-bat_time').first()

        # 기본값 초기화
        price_value = Decimal('-1')
        display_price = '가격정보없음'
        change_rate = None
        formatted_bat_time = '-'
        bat_time_sort_value = 0
        market_cap_display = '-'

        if latest_ticker:
            # 1) 가격 처리 (미국 주식은 소수점 2자리 필수)
            if latest_ticker.price is not None:
                price_value = latest_ticker.price
                display_price = f"{float(price_value):,.2f}"

            # 2) 등락률 처리 (이미 소수점 형태일 것이므로 100을 곱함)
            if latest_ticker.change_rate is not None:
                change_rate = latest_ticker.change_rate * Decimal(100)

            # 3) 시가총액 처리 (미국 시총은 단위가 크므로 가독성 있게 변환 가능)
            if latest_ticker.market_cap:
                m_cap = latest_ticker.market_cap
                if m_cap >= 1_000_000_000_000:  # 1조 달러 이상 (T)
                    market_cap_display = f"${m_cap / 1_000_000_000_000:.2f}T"
                elif m_cap >= 1_000_000_000:  # 10억 달러 이상 (B)
                    market_cap_display = f"${m_cap / 1_000_000_000:.2f}B"
                else:
                    market_cap_display = f"${m_cap / 1_000_000:.2f}M"

            # 4) 시간 처리
            if latest_ticker.bat_time:
                dt = latest_ticker.bat_time
                # 미국 주식이라도 한국 사용자 기준(KST)으로 보여줌
                aware_dt = dt.astimezone(KST) if timezone.is_aware(dt) else timezone.make_aware(dt, KST)
                formatted_bat_time = aware_dt.strftime('%m/%d %H:%M')
                bat_time_sort_value = aware_dt.timestamp()

        # Ticker 데이터가 없을 경우 Candle에서 마지막 종가 백업
        elif not latest_ticker:
            latest_candle = StocksUsCandle.objects.filter(symbol__symbol=symbol).order_by('-date').first()
            if latest_candle:
                price_value = latest_candle.close_price
                display_price = f"{float(price_value):,.2f}"
                # 캔들은 등락률 계산이 필요할 수 있으나 여기서는 단순히 가격만 노출 예시
                formatted_bat_time = latest_candle.date.strftime('%Y/%m/%d') + " (종가)"
                bat_time_sort_value = datetime.datetime.combine(latest_candle.date, datetime.time.min).timestamp()

        stock_list_data.append({
            'name_en': stock['name_en'],
            'name_ko': stock['name_ko'],
            'symbol': symbol,
            'market': stock['market'],
            'sector': stock['sector'],
            'industry': stock['industry'],
            'price': price_value,  # 정렬용 숫자
            'latest_price_display': display_price,  # 화면 표시용
            'change_rate': change_rate,
            'market_cap_display': market_cap_display,
            'updated_at_formatted': formatted_bat_time,
            'updated_at_sort': bat_time_sort_value,
        })

    context = {
        'stock_list': stock_list_data,
        'title': '🇺🇸 미국 주식 실시간 시세 (S&P500 / NASDAQ)'
    }
    return render(request, 'TheaterWinBook/stock_usa_list.html', context)

def stock_rank_usa(request):
    return render(request, 'TheaterWinBook/stock_rank_usa.html')


# 타임존 설정 (settings.py에 정의되어 있다면 가져와서 사용)
KST = pytz.timezone('Asia/Seoul')


def stock_korea_list(request):
    """
    코인 리스트 뷰의 로직을 주식 데이터 구조로 이식.
    Ticker 데이터를 우선하며, 부재 시 Candle 데이터를 활용합니다.
    """
    # 1. 활성화된 주식 리스트 조회
    active_stocks = StocksKrList.objects.filter(is_active=True).values(
        'stock_code', 'stock_name', 'market_type', 'industry'
    )

    stock_list_data = []

    for stock in active_stocks:
        s_code = stock['stock_code']

        # 최신 티커 데이터 조회
        latest_ticker = StocksKrTicker.objects.filter(
            stock_code__stock_code=s_code
        ).order_by('-bat_time').first()

        # 기본값 초기화
        price_value = Decimal('-1')
        display_price = '가격정보없음'
        change_rate = None
        formatted_bat_time = '-'
        bat_time_sort_value = 0

        if latest_ticker:
            print("this is latest_ticker:",latest_ticker.bat_time)
            print("this is ticker_close_price:",latest_ticker.ticker_close_price)
            print("this is ticker_change_rate:",latest_ticker.ticker_change_rate)
            # 1) 가격 처리 (주식은 보통 정수이므로 콤마 처리)
            if latest_ticker.ticker_close_price is not None:
                price_value = latest_ticker.ticker_close_price
                display_price = f"{int(price_value):,}"

            # 2) 등락률 처리
            if latest_ticker.ticker_change_rate is not None:
                change_rate = latest_ticker.ticker_change_rate * Decimal(100)

            # 3) 시간 처리 (분 단위 표시 고도화)
            if latest_ticker.bat_time:
                dt = latest_ticker.bat_time
                aware_dt = dt.astimezone(KST) if timezone.is_aware(dt) else timezone.make_aware(dt, KST)
                formatted_bat_time = aware_dt.strftime('%Y/%m/%d %H:%M')
                bat_time_sort_value = aware_dt.timestamp()

        # Ticker 데이터가 없을 경우 Candle 백업 (코인 로직과 동일)
        elif not latest_ticker:
            latest_candle = StocksKrCandle.objects.filter(stock_code__stock_code=s_code).order_by('-date').first()
            if latest_candle:
                price_value = latest_candle.close_price
                display_price = f"{int(price_value):,}"
                change_rate = latest_candle.change_rate * Decimal(100) if latest_candle.change_rate else 0
                formatted_bat_time = latest_candle.date.strftime('%Y/%m/%d') + " (종가)"
                # 날짜만 있을 경우 타임스탬프 변환
                import datetime
                bat_time_sort_value = datetime.datetime.combine(latest_candle.date, datetime.time.min).timestamp()
        # print("this is name:", stock['stock_name'])
        # print("this is ticker:", s_code)
        # print("this is latest_price_display:", display_price)
        # print("this is updated_at_formatted:", change_rate)
        stock_list_data.append({
            'name': stock['stock_name'],
            'ticker': s_code,
            'market': stock['market_type'],
            'industry': stock['industry'],
            'sort_price': price_value,
            'latest_price_display': display_price,
            'change_rate': change_rate,
            'updated_at_formatted': formatted_bat_time,
            'updated_at_sort': bat_time_sort_value,
        })

    context = {
        'stock_list': stock_list_data,
        'title': '🚀 실시간 주식 시세 (Ticker)'
    }
    return render(request, 'TheaterWinBook/stock_korea_list.html', context)