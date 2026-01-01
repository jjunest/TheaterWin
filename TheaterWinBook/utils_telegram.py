import requests
from django.conf import settings
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .quant_service.quant_analysis import get_mdd_stats
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max
from django.http import JsonResponse


def send_notification_telegram(message, level="INFO", category="주식", chat_id=None):
    """
    텔레그램 알림 공통 함수
    - chat_id가 인자로 들어오면 해당 ID로, 없으면 settings.TELEGRAM_CHAT_ID로 발송
    """
    try:
        token = settings.TELEGRAM_BOT_TOKEN
        # 인자로 받은 chat_id가 없으면 기본 관리자용 CHAT_ID 사용
        target_chat_id = chat_id if chat_id else settings.TELEGRAM_CHAT_ID
    except AttributeError:
        print("[CRITICAL] Telegram settings missing in settings.py")
        return

    API_URL = f"https://api.telegram.org/bot{token}/sendMessage"

    # 레벨별 이모지 및 태그 설정
    icons = {
        "FATAL": "🚨 [치명적 오류]",
        "ERROR": "❌ [데이터 오류]",
        "SUCCESS": "✅ [배치 완료]",
        "INFO": "ℹ️ [알림]",
        "QUANT": "📊 [분석 결과]" # 퀀트 전용 태그 추가
    }

    tag = f"{icons.get(level, '🔔')} [{category}]\n"
    full_message = tag + message

    if len(full_message) > 4000:
        full_message = full_message[:3900] + "\n..."

    try:
        payload = {
            'chat_id': target_chat_id,
            'text': full_message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(API_URL, data=payload, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram failed for chat_id {target_chat_id}: {e}")


# def send_notification_telegram(message, level="INFO", category="주식"):
#     """
#     텔레그램 알림 공통 함수
#     category: 주식, 코인, 시스템 등 구분용
#     """
#     try:
#         token = settings.TELEGRAM_BOT_TOKEN
#         chat_id = settings.TELEGRAM_CHAT_ID
#     except AttributeError:
#         print("[CRITICAL] Telegram settings missing in settings.py")
#         return
#
#     API_URL = f"https://api.telegram.org/bot{token}/sendMessage"
#
#     # 레벨별 이모지 및 태그 설정
#     icons = {
#         "FATAL": "🚨 [치명적 오류]",
#         "ERROR": "❌ [데이터 오류]",
#         "SUCCESS": "✅ [배치 완료]",
#         "INFO": "ℹ️ [알림]"
#     }
#
#     tag = f"{icons.get(level, '🔔')} [{category}]\n"
#     full_message = tag + message
#
#     # 텔레그램 메시지 길이 제한 처리 (4096자)
#     if len(full_message) > 4000:
#         full_message = full_message[:3900] + "\n..."
#
#     try:
#         payload = {
#             'chat_id': chat_id,
#             'text': full_message,
#             'parse_mode': 'Markdown'
#         }
#         response = requests.post(API_URL, data=payload, timeout=5)
#         response.raise_for_status()  # 200이 아니면 예외 발생
#     except Exception as e:
#         print(f"Telegram failed: {e}")