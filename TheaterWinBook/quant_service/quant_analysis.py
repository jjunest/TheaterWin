from datetime import timedelta
from django.utils import timezone
from django.db.models import Max
from ..models_stock_korea import StocksKrList,StocksKrCandle


def get_mdd_stats(stock_code):
    """
    특정 종목의 3, 6, 12개월 MDD(고점 대비 하락률) 계산
    """
    now = timezone.now().date()
    periods = {
        "3M": now - timedelta(days=90),
        "6M": now - timedelta(days=180),
        "12M": now - timedelta(days=365),
    }

    # 현재가 가져오기 (가장 최근 종가)
    latest_candle = StocksKrCandle.objects.filter(stock_code=stock_code).order_data().first()
    if not latest_candle:
        return None

    current_price = float(latest_candle.close_price)
    results = {}

    for label, start_date in periods.items():
        # 해당 기간 최고점 찾기
        max_price = StocksKrCandle.objects.filter(
            stock_code=stock_code,
            date__gte=start_date
        ).aggregate(Max('high_price'))['high_price__max']

        if max_price:
            max_price = float(max_price)
            # 현재가 기준 고점 대비 하락률 (MDD 성격의 지표)
            drop_rate = ((max_price - current_price) / max_price) * 100
            results[label] = {"max": max_price, "drop": round(drop_rate, 2)}

    return results