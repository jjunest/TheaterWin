# this is utils_coin.py 파일

import logging
import requests
import requests
import jwt as pyjwt
import uuid
import hashlib
import time

UPBIT_API_URL = "https://api.upbit.com/v1/ticker"

UPBIT_API_Account_URL = "https://api.upbit.com/v1/accounts"



# get_coin_prices 함수를 수정합니다.
def get_coin_prices(markets):
    """업비트 API에서 지정된 코인들의 시세를 가져오는 함수"""
    # markets 리스트를 콤마로 구분된 문자열로 변환하여 params에 전달
    response = requests.get(UPBIT_API_URL, params={"markets": ",".join(markets)})

    if response.status_code == 200:
        return response.json()
    else:
        # API 오류 발생 시 로그를 남기는 것이 좋습니다.
        print(f"Upbit API 호출 오류: {response.text}")
        return None

def get_upbit_assets(access_key, secret_key):
    print("this is access_key:",access_key)
    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4()),
    }
    jwt_token = pyjwt.encode(payload, secret_key, algorithm='HS256')
    headers = {"Authorization": f'Bearer {jwt_token}'}

    response = requests.get(UPBIT_API_Account_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}
