import requests
import requests
import jwt as pyjwt
import uuid
import hashlib
import time

UPBIT_API_URL = "https://api.upbit.com/v1/ticker"

UPBIT_API_Account_URL = "https://api.upbit.com/v1/accounts"



def get_coin_prices(markets=["KRW-BTC", "KRW-ETH", "KRW-XRP"]):
    """업비트 API에서 지정된 코인들의 시세를 가져오는 함수"""
    response = requests.get(UPBIT_API_URL, params={"markets": ",".join(markets)})

    if response.status_code == 200:
        return response.json()
    else:
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
