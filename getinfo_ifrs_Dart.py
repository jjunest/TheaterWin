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


setting='local'

# (코드참고) https://aidalab.tistory.com/29
def get_stock_list_from_dfr():

    # 한국거래소 상장종목 전체
    dfr_krx_list = fdr.StockListing('KRX')

    # pd.describe_option()
    # print(dfr_krx_list.head())
    print(len(dfr_krx_list))

    stock_list_info_dataframe = pd.DataFrame()
    stock_list_info_dataframe_csv = pd.DataFrame()


    for i in range(len(dfr_krx_list)):
        # print("this is loop")
        stock_code_full = dfr_krx_list.loc[i, "ISU_CD"]
        stock_code = dfr_krx_list.loc[i, "Code"]
        # # 가져올 데이터 # (1-1)저장 날짜는 항상 저장하자
        # # strptime 는 객체를 -> datetime 오브젝트로 변환, strftime는 string형으로 변환
        bat_time = datetime.now()
        # vesting type 1 은 주식
        market_dept = dfr_krx_list.loc[i, "Market"]
        if(market_dept == 'KOSPI'):
            # vesting type 0 = KOSPI
            vesting_type_detail = '0'
        elif (market_dept == 'KOSDAQ'):
            vesting_type_detail = '1'
        elif (market_dept == 'KONEX'):
            vesting_type_detail = '2'
        stock_name_kr = dfr_krx_list.loc[i, "Name"]


        # # 샘플로 [한국비엔씨] 정보부터 끌어오자 https://finance.naver.com/item/main.nhn?code=256840
        # # 1) (종목시세정보) : 날짜, 종가, 거래량, 현재가, 전일가, 시가, 고가, 상한가, 저가, 하한가, 거래량, 거래대금,

        stock_list_info = {
            "bat_time" : bat_time,
            "stock_code_full": stock_code_full,
            "stock_code": stock_code,
            "stock_country": 1,
            "vesting_type": 1,
            #   0은 코스닥이고, 1은 코스피, 2는 코넥스
            "vesting_type_detail": vesting_type_detail,
            "stock_name": stock_name_kr,
            "etc1_string": "",
            "etc2_string": "",
            "etc3_string": "",
            "etc4_string": "",
            "etc5_string": "",
            "etc1_int": 0,
            "etc2_int": 0,
            "etc3_int": 0,
            "etc4_int": 0,
            "etc5_int": 0,
        }
    # stock_list_info_dataframe = stock_list_info_dataframe.append(stock_list_info, ignore_index=True)
    # 사전을 DataFrame으로 변환합니다.
        new_data = pd.DataFrame([stock_list_info])
    # 두 DataFrame을 연결합니다.
        stock_list_info_dataframe = pd.concat([stock_list_info_dataframe, new_data], ignore_index=True)

    # stock_list_info_dataframe = pd.concat([stock_list_info_dataframe, stock_list_info], ignore_index=True)
    print("this is stock_list_info_dataframe:",stock_list_info_dataframe)
        # # (필수) 운영서버에서는 dataframe 컬럼 순서가 바뀌어서, 강제로 아래처럼 코드를 추가
    stock_list_info_dataframe = stock_list_info_dataframe[['stock_code_full', 'stock_code', 'stock_country', 'vesting_type', 'vesting_type_detail', 'stock_name',
             'etc1_string', 'etc2_string', 'etc3_string', 'etc4_string', 'etc5_string', 'etc1_int', 'etc2_int',
             'etc3_int', 'etc4_int', 'etc5_int']]
    insert_info_into_db(stock_list_info_dataframe)

def insert_info_into_db(stock_list_info_dataframe) :
    # print("this is insert_info_into_db() start:",datetime.now())
    try:
        # DB sqlite 위치 구하기
        # stock_summary_info_dataframe
        # pandas 형식의 데이터 타입 -> 날짜 컬럼의 데이터타입을 바꿔주고 -> list로 변환
        print("this is stock_summary_info_dataframe len",len(stock_list_info_dataframe))
        # print("this is stock_list_info_dataframe\n",stock_list_info_dataframe)
        # print("stock_list_info_dataframe(1):", stock_list_info_dataframe )
        # stock_list_info_dataframe['bat_time'] = stock_list_info_dataframe['bat_time'].apply(str)
        stock_list_info_dataframe['stock_code_full'] = stock_list_info_dataframe['stock_code_full'].astype(str)
        # print("this is stock_list_info_dataframe['stock_code_full'] :",stock_list_info_dataframe['stock_code_full'] )
        stock_list_info_dataframe['stock_code'] = stock_list_info_dataframe['stock_code'].astype(str)
        # stock_list_info_dataframe['stock_country'] = stock_list_info_dataframe['stock_country'].astype(str)
        # stock_list_info_dataframe['vesting_type'] = stock_list_info_dataframe['vesting_type'].astype(str)
        # stock_list_info_dataframe['vesting_type_detail'] = stock_list_info_dataframe['vesting_type_detail'].astype(str)
        stock_list_info_dataframe['stock_name'] = stock_list_info_dataframe['stock_name'].astype(str)
        # print("stock_list_info_dataframe(2):", stock_list_info_dataframe )
        # print("stock_list_info_dataframe.values:", stock_list_info_dataframe.values )
        stock_list_info_tolist = stock_list_info_dataframe.values.tolist()
        # print("this is stock_list_info_tolist:", stock_list_info_tolist)
        if setting in 'real':
            # 운영서버용 코드
            sqliteconnection = sqlite3.connect("/home/TheaterWin/db.sqlite3")
        elif setting in 'local':
            # 개발로컬PC용 코드
            sqliteconnection = sqlite3.connect("C:/Users/jjunest/PycharmProjects/TheaterWin/db.sqlite3")
        print("this is connection")
        cursor = sqliteconnection.cursor()
        # sql = 'SET SESSION max_allowed_packet=100M'
        # cursor.execute(sql)
        # stock_summary_info_sample.to_sql('TheaterWinBook_StockSummaryKr',con=sqliteconnection,if_exists='append',index=False,method='multi')

        # executemany 실행 도중 error가 나면, 모두 rollback 이라 삽입이 1개도 되지 않음.
        cursor.executemany("INSERT OR REPLACE INTO TheaterWinBook_StockList("
                           "stock_code_full, stock_code, stock_country, vesting_type, vesting_type_detail, stock_name, "
                           "etc1_string, etc2_string, etc3_string, etc4_string, etc5_string, "
                           "etc1_int, etc2_int,etc3_int, etc4_int, etc5_int"
                           ") VALUES"
                           "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", stock_list_info_tolist)
        # 데이터 프레임의 to_sql함수 : if_exists는 테이블이 존재하면 추가하겠다는 의미.
        # stock_summary_info_dataframe.to_sql('TheaterWinBook_StockSummaryKer3', con = sqliteconnection, if_exists='append', index=False)
        print("this is commit");
        sqliteconnection.commit()

    except sqlite3.Error as error:
        print("Error while connecting to sqlite",error)
        pass

    finally:
        if sqliteconnection :
            sqliteconnection.close()
            print("The Sqlite connection is closed")
        print("this is insert_info_into_db() end")

def remove_comma_string(integer_withcomma):
    integer_withcomma = integer_withcomma.replace(",","").strip()
    # print("this is integer_withcomma",integer_withcomma)
    return integer_withcomma






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


def get_stock_list_from_db():
    print("this is connection")
    if setting in 'real':
        # 운영서버용 코드
        sqliteconnection = sqlite3.connect("/home/TheaterWin/db.sqlite3")
    elif setting in 'local':
        # 개발로컬PC용 코드
        sqliteconnection = sqlite3.connect("C:/Users/jjunest/PycharmProjects/TheaterWin/db.sqlite3")

    cursor = sqliteconnection.cursor()
    # sql = 'SET SESSION max_allowed_packet=100M'
    # cursor.execute(sql)
    # stock_summary_info_sample.to_sql('TheaterWinBook_StockSummaryKr',con=sqliteconnection,if_exists='append',index=False,method='multi')

    # SELECT 문 실행 (코스피 0 전체 목록)
    cursor.execute("SELECT * FROM TheaterWinBook_StockList WHERE vesting_type_detail = '0'")  # 'your_table_name'은 실제 테이블 이름으로 바꿔야 합니다.

    # 결과 가져오기
    stocklists_kospi = cursor.fetchall()
    getinfo_ifrs_dart(stocklists_kospi)

    # SELECT 문 실행 (코스닥 1 전체 목록)
    cursor.execute("SELECT * FROM TheaterWinBook_StockList WHERE vesting_type_detail = '1'")  # 'your_table_name'은 실제 테이블 이름으로 바꿔야 합니다.

    # 결과 가져오기
    stocklists_kosdaq = cursor.fetchall()
    getinfo_ifrs_dart(stocklists_kosdaq)


def getinfo_ifrs_dart(stocklists):
    # 모든 상장된 기업 리스트 불러오기
    api_key = 'a01d762f84b4f7305d16759ae65f6d6f6a98c8b3'
    dart_fss.set_api_key(api_key=api_key)
    crp_list_dart_fss = get_corp_list()

    # 코스피에 대한 정보
    for row in stocklists:
        print("this is test1")
        print(row[2])
        corpInfo = crp_list_dart_fss.find_by_stock_code(row[2])
        corpInfo.extract_fs()
        print(corpInfo)
        break;




if __name__ == '__main__':
    # 데이터프레임 옵션 설정 : 모든 컬럼/row 다보이기
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_seq_items', None)
    pd.set_option('display.max_rows', None)

    print("this is getinfo_ifrs start:",datetime.now())

    get_stock_list_from_db()


    df_krx = fdr.StockListing('KRX')
    # type(df_krx)
    # print("getinfo_fromDart")
    # get_stock_list_from_dfr()
    # stock_list_kor=get_stock_list_kor()
