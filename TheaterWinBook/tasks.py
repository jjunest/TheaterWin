from celery import shared_task
import time
from datetime import datetime


# 기존 Task들은 유지하고, 아래에 새로운 테스트 Task를 추가합니다.

@shared_task
def check_celery_status(param1, param2):
    """
    Celery가 정상 작동하는지 확인하기 위한 "Hello, World!" Task입니다.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1초간 작업 지연 모방
    time.sleep(1)

    # Task 실행 로그를 Worker 터미널에 출력
    print(f"✅ Celery Status Check Task 실행됨!")
    print(f"   입력 파라미터: {param1}, {param2}")
    print(f"   실행 완료 시간: {current_time}")

    # Task 결과를 반환
    return f"Celery is working successfully! Parameters received: {param1} and {param2}."