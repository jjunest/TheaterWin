import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max
from ..models_stock_korea import StocksKrList, StocksKrCandle, StocksKrTicker
from ..models_coins import CoinsUpbitList,CoinsUpbitCandle,CoinsUpbitTicker
import requests
from ..utils_telegram import send_notification_telegram
from django.conf import settings


@csrf_exempt
def telegram_quant_webhook(request):
    QUANT_BOT_TOKEN = settings.TELEGRAM_QUANT_BOT_TOKEN
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            if 'message' in payload:
                chat_id = payload['message']['chat']['id']
                text = payload['message'].get('text', '').strip()

                if text:
                    # 1. '/' 제거 후 코인인지 주식인지 판단 (예: /비트코인 또는 /BTC)
                    query = text.replace('/', '')

                    # 2. 코인 검색 시도
                    coin_response = process_coin_query(query)
                    if coin_response:
                        send_message(QUANT_BOT_TOKEN,chat_id, coin_response)
                    else:
                        # 3. 코인이 없으면 기존 주식 로직 실행
                        stock_response = process_stock_query(query)
                        send_message(chat_id, stock_response)
        except Exception as e:
            print(f"Webhook Error: {e}")

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'fail'}, status=400)


@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            if 'message' in payload:
                chat_id = payload['message']['chat']['id']
                text = payload['message'].get('text', '').strip()

                if text:
                    # 1. '/' 제거 후 코인인지 주식인지 판단 (예: /비트코인 또는 /BTC)
                    query = text.replace('/', '')

                    # 2. 코인 검색 시도
                    coin_response = process_coin_query(query)
                    if coin_response:
                        send_direct_message(chat_id, coin_response)
                    else:
                        # 3. 코인이 없으면 기존 주식 로직 실행
                        stock_response = process_stock_query(query)
                        send_direct_message(chat_id, stock_response)
        except Exception as e:
            print(f"Webhook Error: {e}")

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'fail'}, status=400)


def process_coin_query(query):
    """
    코인명 또는 코인코드로 현재가 및 MDD 계산
    """
    # 1. 코인 찾기 (한글명 또는 KRW-BTC 형태의 코드)
    coin = CoinsUpbitList.objects.filter(coins_name_kor=query).first() or \
           CoinsUpbitList.objects.filter(coins_code=query).first()

    if not coin:
        return None  # 코인이 없으면 None 리턴하여 주식 로직으로 넘김

    # 2. 현재가 가져오기 (CoinsUpbitTicker 활용)
    current_ticker = CoinsUpbitTicker.objects.filter(coins_code=coin).order_by('-bat_time').first()
    if not current_ticker:
        return f"⚠️ {coin.coins_name_kor}의 실시간 가격 데이터가 없습니다."

    curr_price = float(current_ticker.ticker_trade_price)

    # 3. MDD 계산 (최근 1년치 캔들 데이터 기준)
    # 캔들 데이터에서 최고가(coin_high_price)를 가져와서 계산
    now = timezone.now()
    one_year_ago = now - timedelta(days=365)

    high_price_data = CoinsUpbitCandle.objects.filter(
        coins_code=coin,
        coin_candle_datetime_kst__gte=one_year_ago
    ).aggregate(Max('coin_high_price'))

    max_high = float(high_price_data['coin_high_price__max']) if high_price_data['coin_high_price__max'] else 0

    # 4. 메시지 구성
    if max_high > 0:
        mdd = ((curr_price / max_high) - 1) * 100
        mdd_str = f"`{mdd:.2f}%`"
    else:
        mdd_str = "데이터 부족"

    response = [
        f"🪙 *[{coin.coins_name_kor} ({coin.coins_code})]*",
        f"현재가: `{curr_price:,.0f}원`" if curr_price >= 100 else f"현재가: `{curr_price:,.2f}원`",
        f"1년 내 최고점 대비(MDD): {mdd_str}",
        "",
        f"📍 최고가: {max_high:,.0f}원",
        "💡 _MDD가 낮을수록 현재가 저점 구간임을 의미합니다._"
    ]

    return "\n".join(response)



def process_stock_query(query):
    # 1. 종목 찾기 (이름 또는 코드로 검색)
    query = query.replace('/', '')  # 슬래시 제거
    stock = StocksKrList.objects.filter(stock_name=query).first() or \
            StocksKrList.objects.filter(stock_code=query).first()

    if not stock:
        return f"❓ '{query}' 종목을 찾을 수 없습니다."

    # 2. MDD 계산 (3, 6, 12개월)
    now = timezone.now().date()
    periods = {
        "3개월": now - timedelta(days=90),
        "6개월": now - timedelta(days=180),
        "12개월": now - timedelta(days=365),
    }

    # 현재가 가져오기 (Ticker DB 활용)
    current_ticker = StocksKrTicker.objects.filter(stock_code=stock).first()
    if not current_ticker:
        return f"⚠️ {stock.stock_name}의 실시간 가격 데이터가 없습니다."

    curr_price = float(current_ticker.ticker_close_price)

    results = []
    for label, start_date in periods.items():
        # 해당 기간 내 최고가 조회
        high_price_data = StocksKrCandle.objects.filter(
            stock_code=stock,
            date__gte=start_date
        ).aggregate(Max('high_price'))

        max_high = float(high_price_data['high_price__max']) if high_price_data['high_price__max'] else 0

        if max_high > 0:
            # MDD (고점 대비 하락률) 계산: (현재가 / 고점) - 1
            drawdown = ((curr_price / max_high) - 1) * 100
            results.append(f"📍 *{label} 최고점 대비:* `{drawdown:.2f}%` (고점: {int(max_high):,}원)")
        else:
            results.append(f"📍 *{label}:* 데이터 부족")

    # 3. 메시지 구성
    response = [
        f"📊 *[{stock.stock_name} ({stock.stock_code})] 분석*",
        f"현재가: `{int(curr_price):,}원`",
        "",
        *results,
        "",
        "💡 _MDD가 낮을수록 현재가 저점 구간임을 의미합니다._"
    ]

    return "\n".join(response)


def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)




def send_direct_message(chat_id, text):
    """특정 채팅방에 메시지 전송 (기존 함수 변형)"""

    token = settings.TELEGRAM_QUANT_BOT_TOKEN
    # token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    requests.post(url, data=payload)