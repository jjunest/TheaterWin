import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max
from ..models_stock_korea import StocksKrList, StocksKrCandle, StocksKrTicker
import requests
from ..utils_telegram import send_notification_telegram


@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        payload = json.loads(request.body.decode('utf-8'))

        if 'message' in payload:
            chat_id = payload['message']['chat']['id']
            text = payload['message'].get('text', '').strip()

            # 사용자가 "/종목명" 또는 "종목명" 입력 시 처리
            if text:
                response_msg = process_stock_query(text)
                send_direct_message(chat_id, response_msg)

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'fail'}, status=400)


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


def send_direct_message(chat_id, text):
    """특정 채팅방에 메시지 전송 (기존 함수 변형)"""
    from django.conf import settings
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    requests.post(url, data=payload)