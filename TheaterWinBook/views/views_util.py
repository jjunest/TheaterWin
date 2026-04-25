import json
import requests
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max, Min  # Min 추가
from django.conf import settings

# 모델 임포트 (기존 컨텍스트 유지)
from ..models_stock_korea import StocksKrList, StocksKrCandle, StocksKrTicker
from ..models_stock_usa import StocksUsList, StocksUsCandle
from ..models_coins import CoinsUpbitList, CoinsUpbitCandle, CoinsUpbitTicker


@csrf_exempt
def telegram_quant_webhook(request):
    """
    퀀트 봇 웹후크 메인 함수 (6개월 분석 특화)
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

                    # 3. 한국 주식 결과도 없으면 미국 주식 검색
                    if not response:
                        response = process_us_stock_query(query)

                    # 4. 모든 검색 실패 시 최종 메시지
                    if not response:
                        response = f"❓ '{query}'에 해당하는 종목을 찾을 수 없습니다."

                    send_direct_message(chat_id, response)
        except Exception as e:
            print(f"Webhook Error: {e}")

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'fail'}, status=400)


def process_coin_query(query):
    """코인 6개월 최고/최저 대비 분석"""
    coin = CoinsUpbitList.objects.filter(coins_name_kor=query).first() or \
           CoinsUpbitList.objects.filter(coins_code=query).first()

    if not coin:
        return None

    current_ticker = CoinsUpbitTicker.objects.filter(coins_code=coin).order_by('-bat_time').first()
    if not current_ticker:
        return f"⚠️ {coin.coins_name_kor}의 실시간 가격 데이터가 없습니다."

    curr_price = float(current_ticker.ticker_trade_price)
    six_months_ago = timezone.now() - timedelta(days=180)

    # 6개월 내 최고가 및 최저가 조회
    stats = CoinsUpbitCandle.objects.filter(
        coins_code=coin,
        coin_candle_datetime_kst__gte=six_months_ago
    ).aggregate(max_p=Max('coin_high_price'), min_p=Min('coin_low_price'))

    max_p = float(stats['max_p']) if stats['max_p'] else 0
    min_p = float(stats['min_p']) if stats['min_p'] else 0

    return format_summary_message(
        name=coin.coins_name_kor,
        symbol=coin.coins_code,
        curr=curr_price,
        high=max_p,
        low=min_p,
        currency="원"
    )


def process_stock_query(query):
    """한국 주식 6개월 최고/최저 대비 분석"""
    stock = StocksKrList.objects.filter(stock_name=query).first() or \
            StocksKrList.objects.filter(stock_code=query).first()

    if not stock:
        return None

    current_ticker = StocksKrTicker.objects.filter(stock_code=stock).first()
    if not current_ticker:
        return f"⚠️ {stock.stock_name}의 실시간 가격 데이터가 없습니다."

    curr_price = float(current_ticker.ticker_close_price)
    six_months_ago = timezone.now().date() - timedelta(days=180)

    # 6개월 내 최고가 및 최저가 조회
    stats = StocksKrCandle.objects.filter(
        stock_code=stock,
        date__gte=six_months_ago
    ).aggregate(max_p=Max('high_price'), min_p=Min('low_price'))

    max_p = float(stats['max_p']) if stats['max_p'] else 0
    min_p = float(stats['min_p']) if stats['min_p'] else 0

    return format_summary_message(
        name=stock.stock_name,
        symbol=stock.stock_code,
        curr=curr_price,
        high=max_p,
        low=min_p,
        currency="원"
    )


def process_us_stock_query(query):
    """미국 주식 6개월 최고/최저 대비 분석"""
    stock = StocksUsList.objects.filter(symbol=query).first() or \
            StocksUsList.objects.filter(name_en__icontains=query).first()

    if not stock:
        return None

    latest_candle = StocksUsCandle.objects.filter(symbol=stock).order_by('-date').first()
    if not latest_candle:
        return f"⚠️ {stock.symbol}의 가격 데이터가 존재하지 않습니다."

    curr_price = float(latest_candle.close_price)
    six_months_ago = latest_candle.date - timedelta(days=180)

    # 6개월 내 최고가 및 최저가 조회
    stats = StocksUsCandle.objects.filter(
        symbol=stock,
        date__gte=six_months_ago
    ).aggregate(max_p=Max('high_price'), min_p=Min('low_price'))

    max_p = float(stats['max_p']) if stats['max_p'] else 0
    min_p = float(stats['min_p']) if stats['min_p'] else 0

    return format_summary_message(
        name=stock.name_en,
        symbol=stock.symbol,
        curr=curr_price,
        high=max_p,
        low=min_p,
        currency="$"
    )


def format_summary_message(name, symbol, curr, high, low, currency):
    """메시지 포맷팅 공통 로직"""
    if high == 0 or low == 0:
        return f"📊 *[{name} ({symbol})]*\n최근 6개월 데이터가 부족합니다."

    # 1. 최고가 대비 현재가 (MDD/하락폭)
    diff_from_high = ((curr / high) - 1) * 100
    # 2. 최저가 대비 현재가 (상승폭)
    diff_from_low = ((curr / low) - 1) * 100

    # 화폐 기호 위치 처리
    curr_fmt = f"{curr:,.2f}{currency}" if currency == "원" else f"{currency}{curr:,.2f}"
    high_fmt = f"{high:,.2f}{currency}" if currency == "원" else f"{currency}{high:,.2f}"
    low_fmt = f"{low:,.2f}{currency}" if currency == "원" else f"{currency}{low:,.2f}"

    response = [
        f"📊 *[{name} ({symbol})]*",
        f"현재가: `{curr_fmt}`",
        "",
        f"🔍 *최근 6개월 분석*",
        f"📈 최고가 대비: `{diff_from_high:.2f}%` (고점: {high_fmt})",
        f"📉 최저가 대비: `+{diff_from_low:.2f}%` (저점: {low_fmt})",
        "",
        "💡 _최고가 대비 하락폭이 크고 최저가 대비 상승폭이 적을수록 바닥권일 확률이 높습니다._"
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