import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os


# Firebase 초기화 (앱이 시작될 때 한 번만 실행되도록 설정 필요, 여기선 함수 내 체크)
def initialize_firebase():
    if not firebase_admin._apps:
        # manage.py와 같은 위치에 있는 키 파일 경로
        cred_path = os.path.join(settings.BASE_DIR, 'firebase-adminsdk.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)


def send_push_notification(token, title, body):
    """
    특정 기기(token)로 푸시 알림을 보냅니다.
    """
    initialize_firebase()

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,  # 앱에서 받은 기기 고유 토큰
        )
        response = messaging.send(message)
        print('✅ 성공적으로 메시지 전송:', response)
        return True
    except Exception as e:
        print('❌ 메시지 전송 실패:', e)
        return False