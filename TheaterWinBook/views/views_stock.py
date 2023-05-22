from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.encoding import smart_text

from ..forms import UserForm, LoginForm, TheaterWinBookRecordForm, TheaterWinQuestionForm
from ..models import Post, TheaterWinBookRecord, TheaterWinQuestion, TheaterWinQuestionInfo, TheaterWinQuestionReply, Full_Chatting_Message, TheaterWinBookRecordInfo, TheaterWinBookRecordReply, StockSummaryKr, StockList
from django.contrib import messages
from django.contrib.messages import get_messages
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F
from django.db.models import Max, Min
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page
import traceback
from django.shortcuts import render
from django.utils.safestring import mark_safe
import json



# stock_rank
def stock_rank(request):
    return render(request, 'TheaterWinBook/stock_rank.html')


def stock_rank_pop(request, rank_name, market_sum_percent):
    print("this is ranktype:", rank_name)
    latest_date = StockSummaryKr.objects.filter().latest('info_date')
    print("this is lastest_date:", latest_date.info_date)
    # latest_date_list = list(latest_date)
    # print("this is latest_date_list", latest_date_list)
    latest_date = StockSummaryKr.objects.filter().latest('info_date')


    # Global Condition (like market_sum_percentage)
    print("this is market_sum_percent:" + market_sum_percent)
    market_sum_percent = int(market_sum_percent)
    total_rows = StockSummaryKr.objects.count()
    print ("this is total_rows:", str(total_rows))
    num_rows = int(total_rows * market_sum_percent / 100)
    print ("this is num_rows:" , str(num_rows))

    StockSummaryKr_MarketSumCondition = StockSummaryKr.objects.raw("SELECT * FROM TheaterWinBook_stocksummarykr "
                                       "WHERE info_date = (SELECT info_date FROM TheaterWinBook_stocksummarykr "
                                       "ORDER BY info_date DESC LIMIT 1) ORDER BY STOCK_MARKET_SUM DESC LIMIT %s", [num_rows])
    print("this is num_rows(tobe) ", str(len(list(StockSummaryKr_MarketSumCondition))))

    # rank name 에 따라 top stock 10 개 리스트를 추려서 화면에 뿌려줌
    if rank_name == "marketsum":
        top_stock = StockSummaryKr.objects.raw("SELECT * FROM TheaterWinBook_stocksummarykr "
                                            "WHERE info_date = (SELECT info_date FROM TheaterWinBook_stocksummarykr "
                                            "ORDER BY info_date DESC LIMIT 1) "
                                            "AND 1=1 "
                                            "ORDER BY STOCK_MARKET_SUM DESC LIMIT 10")

    # rank name(per_desc) 에 따라 top stock 10 개 리스트를 추려서 화면에 뿌려줌
    if rank_name == "per_desc":
        top_stock = StockSummaryKr.objects.raw("SELECT * FROM TheaterWinBook_stocksummarykr "
                                            "WHERE info_date = (SELECT info_date FROM TheaterWinBook_stocksummarykr "
                                            "ORDER BY info_date DESC LIMIT 1) "
                                            "AND 1=1 "
                                            "AND typeof(stock_per) = 'real'"
                                            "ORDER BY stock_per DESC LIMIT 10")

    for p in top_stock :
        print("%s 번째, %s" % (p.stock_name,p))
    top_stock_list = list(top_stock)

    return render(request, 'TheaterWinBook/stock_rank_pop.html',{"top_stock": top_stock})
    # return render(request, 'TheaterWinBook/stock_rank_pop.html',{"top10": top10_result})


def stock_list_kospi(request):
    print("this is stock_list_kospi")
    # rank name 에 따라 top stock 10 개 리스트를 추려서 화면에 뿌려줌
    top_stock = StockList.objects.raw('SELECT * FROM TheaterWinBook_StockList A LEFT OUTER JOIN (SELECT * FROM TheaterWinBook_stocksummarykr GROUP BY STOCK_CODE HAVING MAX(INFO_DATE)) B ON A.stock_code = B.stock_code ORDER BY B.STOCK_MARKET_SUM DESC')
    return render(request, 'TheaterWinBook/stock_list_kospi.html',{"top_stock": top_stock})


def stock_detail_kor(request, stock_code):
    stock_code = stock_code
    print("this is stock_detail page, stock_code:",stock_code)
    stock_detail = StockSummaryKr.objects.raw('SELECT * FROM TheaterWinBook_stocksummarykr WHERE '
                                       'info_date = (SELECT info_date FROM TheaterWinBook_stocksummarykr '
                                       'ORDER BY info_date DESC LIMIT 1) and STOCK_CODE = %s',[stock_code])

    print("this is stock_detail:",stock_detail)
    # question_pk = question_pk
    # print("this is question_pk" + question_pk)

    # return render(request, 'TheaterWinBook/stock_detail.html',
    #               {'question_record': target_record, 'form': form, 'is_record_owner': is_record_owner,
    #                'thumbup_count': thumbup_count, 'thumbdown_count': thumbdown_count, 'target_replys': target_replys,
    #                'login_user': login_user})

    return render(request, 'TheaterWinBook/stock_detail_kor.html', {'stock_detail': stock_detail} )


