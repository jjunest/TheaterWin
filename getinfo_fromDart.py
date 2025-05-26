import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy
import re
import datetime
import sqlite3
from datetime import datetime
from datetime import date
import time
import logging
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', "TheaterWin.settings")
import django
django.setup()
from TheaterWinBook.models import FullvestingApi
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import requests
from io import BytesIO
import zipfile
import xmltodict
import dart_fss as dart_fss
from dart_fss import get_corp_list
from sklearn import svm


# (코드참고) https://aidalab.tistory.com/29
def get_stock_list_from_dfr():

    # 한국거래소 상장종목 전체
    df_krx = fdr.StockListing('KRX')
    pd_df_krx =pd.DataFrame(df_krx)

    # pd.describe_option()
    print(pd_df_krx.head())
    print(len(df_krx))





# (코드참고) https://aidalab.tistory.com/29
def get_stock_list_kor():
    print('this is get_stock_list_kor() start')
    # 종목코드는 거래소 파일에서 읽어옴. 네이버주가총액은 etf까지 존재, 거래소파일은 fullvestapi 폴더와 동일위치
    # 운영서버 코드
    # stock_list_kospi_csv = pd.read_csv("/home/fullvestapi/kospi_list.csv", encoding='euc-kr')
    # stock_list_kosdaq_csv = pd.read_csv("/home/fullvestapi/kosdaq_list.csv", encoding='euc-kr')
    # 개발로컬 PC 코드
    stock_list_kospi_csv = pd.read_csv("kospi_list.csv", encoding='euc-kr')
    stock_list_kosdaq_csv = pd.read_csv("kosdaq_list.csv", encoding='euc-kr')

    stock_list_kospi_csv = stock_list_kospi_csv.iloc[:,[1,3]]
    stock_list_kospi_csv['type'] = 0
    stock_list_kospi_csv.columns = ['stock_code','stock_name_kr','type']
    stock_list_kospi_csv['stock_code'] = stock_list_kospi_csv['stock_code'].astype('str').str.zfill(6)
    stock_list_kospi_csv = stock_list_kospi_csv[['type','stock_code','stock_name_kr']]

    # print(stock_list_kospi_csv)
    stock_list_kosdaq_csv = stock_list_kosdaq_csv.iloc[:,[1,3]]
    stock_list_kosdaq_csv['type'] = 1
    stock_list_kosdaq_csv.columns = ['stock_code','stock_name_kr','type']
    stock_list_kosdaq_csv = stock_list_kosdaq_csv[['type','stock_code','stock_name_kr']]
    stock_list_kosdaq_csv['stock_code'] = stock_list_kosdaq_csv['stock_code'].astype('str').str.zfill(6)
    # concat을 하면, 앞의 index가 중복이 될 수 있으므로, index를 새롭게 만들어주는 조건을 넣어야 함
    stock_list_kr = pd.concat([stock_list_kospi_csv,stock_list_kosdaq_csv], ignore_index=True)
    stock_list_kr.columns = ['type','stock_code','stock_name_kr']

    print('this is get_stock_list_kor() end')
    return stock_list_kr





def getinfo_fromDart():
    # 샘플: https://opendart.fss.or.kr/api/company.json?crtfc_key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&corp_code=00126380
    # 인증키 : a01d762f84b4f7305d16759ae65f6d6f6a98c8b3
    # https://opendart.fss. or.kr / api / corpCode.xml
    # GET방식 호출 테스트
    # url = 'https://opendart.fss.or.kr/api/company.json'  # 접속할 사이트주소 또는 IP주소를 입력한다
    # data = {'crtfc_key': 'a01d762f84b4f7305d16759ae65f6d6f6a98c8b3', 'corp_code':'00126380'}  # 요청할 데이터
    # response = web_request(method_name='GET', url=url, dict_data=data)
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    data = {'crtfc_key': 'a01d762f84b4f7305d16759ae65f6d6f6a98c8b3'}  # 요청할 데이터
    # data_xml = zipfile.ZipFile(BytesIO(res.content))
    # response = web_request(method_name='GET', url=url, dict_data=data)

    # 종목 코드
    # Open DART API KEY 설정
    api_key = 'a01d762f84b4f7305d16759ae65f6d6f6a98c8b3'
    dart_fss.set_api_key(api_key=api_key)
    corp_list = dart_fss.get_corp_list()
    # print(corp_list)
    dart_all = dart_fss.api.filings.get_corp_code()
    df = pd.DataFrame(dart_all)
    print("데이터프레임 길이:",len(df))
    # 'Age' 열에서 None 값을 가진 행 추출
    df_filtered = df[df['stock_code'].notna()]
    print("데이터프레임 정제후길이:",len(df_filtered))
    # print(df_filtered)


    #휴대폰 / 코스피시장 : Y / 코스닥시장 : K
    marketY = corp_list.find_by_sector('%',market='Y')
    print(marketY)

    # filtered_data = list(filter(lambda x: x['stock_code'] is not None, data))
    # print(filtered_data)

    # print(df.head(300))


    # print(corp_list.corps)
    # pd.DataFrame(corp_list)

def get_page_content(url):
    html_text = requests.get(url)
    page_soup = BeautifulSoup(html_text.content.decode('euc-kr', 'replace'), 'html.parser')

    return page_soup


def web_request(method_name, url, dict_data, is_urlencoded=True):
    """Web GET or POST request를 호출 후 그 결과를 dict형으로 반환 """
    method_name = method_name.upper()  # 메소드이름을 대문자로 바꾼다
    if method_name not in ('GET', 'POST'):
        raise Exception('method_name is GET or POST plz...')

    if method_name == 'GET':  # GET방식인 경우
        response = requests.get(url=url, params=dict_data)
    elif method_name == 'POST':  # POST방식인 경우
        if is_urlencoded is True:
            response = requests.post(url=url, data=dict_data,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'})
        else:
            response = requests.post(url=url, data=json.dumps(dict_data), headers={'Content-Type': 'application/json'})

    dict_meta = {'status_code': response.status_code, 'ok': response.ok, 'encoding': response.encoding,
                 'Content-Type': response.headers['Content-Type']}
    if 'json' in str(response.headers['Content-Type']):  # JSON 형태인 경우
        return {**dict_meta, **response.json()}
    else:  # 문자열 형태인 경우
        return {**dict_meta, **{'text': response.text}}


if __name__ == '__main__':
    # 데이터프레임 옵션 설정 : 모든 컬럼/row 다보이기
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_seq_items', None)
    pd.set_option('display.max_rows', None)

    print("this is getinfo_db_summary_everyday start:",datetime.now())
    stockcode_url = "https://finance.naver.com/sise/sise_market_sum.nhn?&page="
    # print('오늘 네이버주가 끌어왓습니다!!! 네이버 주가는 : '+get_price("005930"))

    df_krx = fdr.StockListing('KRX')
    # type(df_krx)
    # print("getinfo_fromDart")
    get_stock_list_from_dfr()
    # stock_list_kor=get_stock_list_kor()

    # insert_info_into_db()
    # print(df_krx)
    # df = fdr.DataReader('001250', '2023')
    # df.head(10)
    # print(df)
    # df = fdr.DataReader('068270', '2017')
    # plt.plot([1, 2, 3, 4])
    # plt.ylabel('some numbers')
    # plt.show()

