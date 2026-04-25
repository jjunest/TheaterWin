import json
import requests
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max
from django.conf import settings

# 모델 임포트 (기존 컨텍스트 유지)
from ..models_stock_korea import StocksKrList, StocksKrCandle, StocksKrTicker
from ..models_stock_usa import StocksUsList, StocksUsCandle
from ..models_coins import CoinsUpbitList, CoinsUpbitCandle, CoinsUpbitTicker


@csrf_exempt
def telegram_quant_webhook(request):
    """
    퀀트 봇 웹후크 메인 함수
    검색 순서: 코인 -> 한국 주식 -> 미국 주식
    """
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            if 'message' in payload:
                chat_id = payload['message']['chat']['id']
                text = payload['message'].get('text', '').strip()

                if text:
                    query = text.replace('/', '').upper()

                    # 1. 코인 검색 시도
                    response = process_coin_query(query)

                    # 2. 코인 결과가 없으면 한국 주식 검색
                    if not response:
                        response = process_stock_query(query)

                    # 3. 한국 주식 결과도 없으면(None 리턴 시) 미국 주식 검색
                    if not response:
                        response = process_us_stock_query(query)

                    # 4. 모든 검색 실패 시 최종 메시지
                    if not response:
                        response = f"❓ '{query}'에 해당하는 코인, 한국주식, 미국주식을 찾을 수 없습니다."

                    send_direct_message(chat_id, response)
        except Exception as e:
            print(f"Webhook Error: {e}")

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'fail'}, status=400)


def process_coin_query(query):
    """코인명 또는 코인코드로 현재가 및 MDD 계산"""
    coin = CoinsUpbitList.objects.filter(coins_name_kor=query).first() or \
           CoinsUpbitList.objects.filter(coins_code=query).first()

    if not coin:
        return None  # 검색 결과 없으면 None 리턴

    current_ticker = CoinsUpbitTicker.objects.filter(coins_code=coin).order_by('-bat_time').first()
    if not current_ticker:
        return f"⚠️ {coin.coins_name_kor}의 실시간 가격 데이터가 없습니다."

    curr_price = float(current_ticker.ticker_trade_price)
    now = timezone.now()
    one_year_ago = now - timedelta(days=365)

    high_price_data = CoinsUpbitCandle.objects.filter(
        coins_code=coin,
        coin_candle_datetime_kst__gte=one_year_ago
    ).aggregate(Max('coin_high_price'))

    max_high = float(high_price_data['coin_high_price__max']) if high_price_data['coin_high_price__max'] else 0
    mdd = ((curr_price / max_high) - 1) * 100 if max_high > 0 else 0

    response = [
        f"🪙 *[{coin.coins_name_kor} ({coin.coins_code})]*",
        f"현재가: `{curr_price:,.0f}원`" if curr_price >= 100 else f"현재가: `{curr_price:,.2f}원`",
        f"1년 내 최고점 대비(MDD): `{mdd:.2f}%`",
        "",
        f"📍 52주 최고가: `{max_high:,.0f}원`",
        "💡 _MDD가 낮을수록 현재가 저점 구간임을 의미합니다._"
    ]
    return "\n".join(response)


def process_stock_query(query):
    """한국 주식 검색 및 기간별 분석"""
    stock = StocksKrList.objects.filter(stock_name=query).first() or \
            StocksKrList.objects.filter(stock_code=query).first()

    if not stock:
        return None  # 검색 결과 없으면 None 리턴

    current_ticker = StocksKrTicker.objects.filter(stock_code=stock).first()
    if not current_ticker:
        return f"⚠️ {stock.stock_name}의 실시간 가격 데이터가 없습니다."

    curr_price = float(current_ticker.ticker_close_price)
    now = timezone.now().date()

    # 기간별 MDD 계산
    periods = {"3개월": 90, "6개월": 180, "12개월": 365}
    results = []

    for label, days in periods.items():
        start_date = now - timedelta(days=days)
        high_data = StocksKrCandle.objects.filter(stock_code=stock, date__gte=start_date).aggregate(Max('high_price'))
        max_h = float(high_data['high_price__max']) if high_data['high_price__max'] else 0

        if max_h > 0:
            dd = ((curr_price / max_h) - 1) * 100
            results.append(f"📍 *{label} MDD:* `{dd:.2f}%` (고점: {int(max_h):,}원)")
        else:
            results.append(f"📍 *{label}:* 데이터 부족")

    response = [
        f"📊 *[{stock.stock_name} ({stock.stock_code})]*",
        f"현재가: `{int(curr_price):,}원`",
        "",
        *results,
        "",
        "💡 _MDD가 낮을수록 현재가 저점 구간임을 의미합니다._"
    ]
    return "\n".join(response)


def process_us_stock_query(query):
    """
    미국 주식 검색 및 기간별(1, 3, 6개월) 분석 추가
    """
    stock = StocksUsList.objects.filter(symbol=query).first() or \
            StocksUsList.objects.filter(name_en__icontains=query).first()

    if not stock:
        return None  # 최종적으로 검색 결과 없으면 None

    latest_candle = StocksUsCandle.objects.filter(symbol=stock).order_by('-date').first()
    if not latest_candle:
        return f"⚠️ {stock.symbol}의 가격 데이터가 존재하지 않습니다."

    curr_price = float(latest_candle.close_price)
    latest_date = latest_candle.date

    # 요청하신 기간별 최고가 분석 (1, 3, 6개월)
    periods = {"1개월": 30, "3개월": 90, "6개월": 180, "12개월": 365}
    mdd_results = []

    for label, days in periods.items():
        start_date = latest_date - timedelta(days=days)
        high_data = StocksUsCandle.objects.filter(symbol=stock, date__gte=start_date).aggregate(Max('high_price'))
        max_h = float(high_data['high_price__max']) if high_data['high_price__max'] else 0

        if max_h > 0:
            dd = ((curr_price / max_h) - 1) * 100
            mdd_results.append(f"✅ *{label} MDD:* `{dd:.2f}%` (고점: ${max_h:,.2f})")
        else:
            mdd_results.append(f"✅ *{label}:* 데이터 부족")

    response = [
        f"🇺🇸 *[{stock.name_en} ({stock.symbol})]*",
        f"최근 종가: `${curr_price:,.2f}` (`{latest_date}` 기준)",
        "",
        *mdd_results,
        "",
        f"🏛️ 시장: {stock.market} | 섹터: {stock.sector or 'N/A'}",
        "💡 _미국 주식은 전 영업일 종가 기준으로 분석됩니다._"
    ]
    return "\n".join(response)


def send_direct_message(chat_id, text):
    """텔레그램 메시지 전송 함수"""
    token = settings.TELEGRAM_QUANT_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Send Error: {e}")