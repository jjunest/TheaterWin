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


@login_required(login_url='/login_view')
def winbook_calendar(request):
    # 로그인된 user를 확인하고
    login_user_name = request.user
    winbook_user_result = TheaterWinBookRecord.objects.filter(user_name=login_user_name).order_by('buy_date',
                                                                                                  '-pk')
    winbook_user_result_json = serializers.serialize('json', winbook_user_result)
    # winbook_user_result_json =JsonResponse({"models_to_return": list(winbook_user_result)})
    # print(winbook_user_result)
    # winbook_user_result_json = json.dumps(list(winbook_user_result), ensure_ascii=False, default=str)
    print("this is json:" + winbook_user_result_json)
    return render(request, 'TheaterWinBook/winbook_calendar.html',
                  {"winbook_user_result_json": winbook_user_result_json})



@login_required(login_url='/login_view')
def winbook_list(request):
    datepicker_start = request.GET.get('datepicker_start', None)
    datepicker_end = request.GET.get('datepicker_end', None)
    pagenum = request.GET.get('pagenum', 1)
    # GET 으로 받은 파라미터는 integer가 아니라, int 처리해줘야 한다....
    pagenum = int(pagenum)

    print("this is datepicker_start:", datepicker_start, "and datepicker_end:", datepicker_end)
    # 신규 글 number를 메세지로 받아오기
    storage = get_messages(request)
    # 만약에 new_winbook_pk 의 디폴트 값을 설정하자..
    new_winbook_pk = 0
    new_winbook_check = 'n'
    for message in storage:
        print(message)
        # 메세지 중에서, insert_success 메세지가 있으면, extra tag에서 데이터를 가져온다.
        if str(message) == "insert_success":
            new_winbook_pk = message.extra_tags
            # 개인적으로 check 컨텍스트도 넘겨주자..
            new_winbook_check = 'y'
        else:
            print("메세지 도달 실패")

    # 로그인된 user를 확인하고
    login_user_name = request.user
    if (datepicker_start == None and datepicker_end == None):
        datepicker_start = '2000-01-01'
        datepicker_end = '2100-01-01'
        winbook_user_result = TheaterWinBookRecord.objects.filter(user_name=login_user_name).order_by('-buy_date',
                                                                                                      '-pk')
    else:
        winbook_user_result = TheaterWinBookRecord.objects.filter(user_name=login_user_name,
                                                                  buy_date__range=[datepicker_start,
                                                                                   datepicker_end]).order_by(
            '-buy_date',
            '-pk')

    winbook_user_result_list = list(winbook_user_result)
    total_records_count = len(winbook_user_result_list)
    total_net_profit = 0
    yet_total = 0
    for listobject in winbook_user_result_list:
        win_check = listobject.win_check
        batting_money = listobject.batting_money
        batting_ratio = listobject.batting_ratio
        folder_num = listobject.folder_num
        net_profit = 0
        yet_money = 0
        if win_check == 0:
            net_profit = -(batting_money)
        elif win_check == 1:
            net_profit = ((batting_ratio * batting_money) - (batting_money))
            # 미적중은 total에 카운팅하지 않기로 했다.
        elif win_check == 2:
            yet_money = ((batting_ratio * batting_money) - (batting_money))
        # net_profit = ((batting_ratio * batting_money) - (batting_money))
        total_net_profit += net_profit
        yet_total += yet_money
    total_net_profit = format(int(total_net_profit), ',')
    yet_total = format(int(yet_total), ',')
    # 현재까지 순수익 구하기.

    # 페이지 nator를 사용해서 10개씩 페이지로 만들기.
    paginator = Paginator(winbook_user_result, 10)
    print("this is paginator:", paginator)
    try:
        database_list_result_page = paginator.page(pagenum)
        database_list_result_page.page_range = paginator.page_range
        print("this is database_list_result_page page:", database_list_result_page.page_range)
        total_page_number = paginator.num_pages
        # 페이지에 보이는 페이지 numer의 수
        pagenum_in_per_page = int(3)
        start_page = ((pagenum - 1) // pagenum_in_per_page) * pagenum_in_per_page + 1
        end_page = start_page + pagenum_in_per_page
        if end_page > total_page_number:
            end_page = total_page_number + 1
        print("this is start_page:", start_page)
        database_list_result_page.start_page = int(start_page)
        database_list_result_page.end_page = int(end_page)
        print("this is end_page:", database_list_result_page.end_page)
        database_list_result_page.custom_page_range = range(database_list_result_page.start_page,
                                                            database_list_result_page.end_page)
        database_list_result_page.pagenum = pagenum
        database_list_result_page.total_page_number = total_page_number
    except PageNotAnInteger:
        print("this is not an integer")
        database_list_result_page = paginator.page(1)
    except Exception as e:
        print("this is page exception")
        # 에러가 나면 다시 1페이지로로 돌려주자.
        trace_back = traceback.format_exc()
        message = str(e) + " " + str(trace_back)
        return redirect('winbook_list')

    return render(request, 'TheaterWinBook/winbook_list.html',
                  {"database_list_result_page": database_list_result_page, "new_winbook_pk": new_winbook_pk,
                   'new_winbook_check': new_winbook_check, "total_net_profit": total_net_profit,
                   "yet_total": yet_total, "datepicker_start": datepicker_start, "datepicker_end": datepicker_end,
                   "total_records_count": total_records_count})





@login_required(login_url='/login_view')
def winbook_detail(request, record_pk):
    # 1. 해당 리코드의 공개 여부를 확인함.
    winbook_record = TheaterWinBookRecord.objects.get(pk=record_pk)
    winbook_record.hit_count = winbook_record.hit_count + 1
    winbook_record.save()
    share_check = winbook_record.share_check
    form = TheaterWinBookRecordForm(instance=winbook_record)

    # 추천과 비추천 숫자를 세자. FOREIGNER 외래키를 찾을 때에는 get이 아니라, filter 를 사용해야 한다.
    thumbup_count = TheaterWinBookRecordInfo.objects.filter(record_fk=winbook_record, record_thumbup=1).count()
    thumbdown_count = TheaterWinBookRecordInfo.objects.filter(record_fk=winbook_record, record_thumbdown=1).count()
    target_replys = TheaterWinBookRecordReply.objects.filter(record_fk=winbook_record)
    if share_check == 1:
        #공개로 설정 시에는 전부 공개

        return render(request, 'TheaterWinBook/winbook_detail.html', {'winbook_record': winbook_record, "form": form, "thumbup_count":thumbup_count, "thumbdown_count":thumbdown_count, "target_replys":target_replys})
    elif share_check ==0:
        login_user_name = request.user
        record_writer = winbook_record.user_name
        if login_user_name == record_writer:
            # 비공개시 그것이 내것이면 접근가능하게 하고
            return render(request, 'TheaterWinBook/winbook_detail.html',
                          {'winbook_record': winbook_record, "form": form,"thumbup_count":thumbdown_count, "thumbdown_count":thumbdown_count, "target_replys":target_replys})
        else:
            #  유저가 확인이 안되면 에러 페이지로 넘김.
            return render(request, 'TheaterWinBook/error_wronguser.html')




@login_required(login_url='/login_view')
def winbook_modify(request):
    record_pk = request.GET.get("record_pk", "")
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = TheaterWinBookRecord.objects.get(pk=record_pk)
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    if target_record.user_name == login_user:
        if request.method == "POST":
            # create a form instance and populate it with data from the request:
            record_pk = request.POST.get("record_pk", "")
            target_modify_record = TheaterWinBookRecord.objects.get(pk=record_pk)
            form = TheaterWinBookRecordForm(request.POST,
                                            instance=target_modify_record)  # PostForm으로 부터 받은 데이터를 처리하기 위한 인스턴스 생성
            if form.is_valid():  # 폼 검증 메소드
                inputForm = form.save(commit=False)  # 오브젝트를 form으로 부터 가져오지만, 실제로 DB반영은 하지 않는다.
                # 가져 온 후 데이터 처리를 ㅐㅎ도 된다.
                inputForm.user_name = request.user
                # inputForm 저장하기
                inputForm.save()
                # 저장한 후에 pk 값 가져오기
                print("this is after modifying records pk :", inputForm.pk)
                modify_winbook_pk = inputForm.pk
                # 정보를 성공적으로 입력한 후에는, 메세지에 방금 입력된 pk값을 담아서 보내기
                return redirect('winbook_detail', record_pk=modify_winbook_pk)
            else:
                messages.error(request, "please enter right field")
        else:
            #   정상적으로 modify로 이동시켜준다.
            form = TheaterWinBookRecordForm(instance=target_record)  # forms.py의 PostForm 클래스의 인스턴스
            return render(request, 'TheaterWinBook/winbook_modify.html',
                          {'form': form, 'record_pk': record_pk, 'target_record': target_record})

    else:
        #  유저가 확인이 안되면 에러 페이지로 넘김.
        return render(request, 'TheaterWinBook/error_wronguser.html')


@login_required(login_url='/login_view')
def list_usercheck(request):
    print("this is user_check")
    # request parameter 로 winbook.pk를 받아온다.
    record_pk = request.POST.get("record_pk", "")
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = TheaterWinBookRecord.objects.get(pk=record_pk)
    print(target_record.user_name)
    print(request.user)
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    usercheck_success = "fail"
    if (target_record.user_name == login_user):
        # pk번호를 기준으로 삭제를 하자.
        usercheck_success = "success";
    else:
        usercheck_success = "fail";
    return HttpResponse(json.dumps({'usercheck_success': usercheck_success}), content_type="application/json")


@login_required(login_url='/login_view')
def list_delete(request):
    # request parameter 로 winbook.pk를 받아온다.
    record_pk = request.POST.get("record_pk", "")
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = TheaterWinBookRecord.objects.get(pk=record_pk)
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    delete_success = "fail"
    if target_record.user_name == login_user:
        print('this is login user');
        # pk번호를 기준으로 삭제를 하자.
        target_record.delete()
        delete_success = "success";
    else:
        print("this is not equal login user")

    return HttpResponse(json.dumps({'delete_success': delete_success}), content_type="application/json")

    # 일치시에만 삭제 시작하고,

    # else 일치하지 않으면, 잘못된 접근 및 로그아웃 화면으로 넘기자.

#
@login_required(login_url='/login_view')
def winbook_insert(request):
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        print("this is post1")
        form = TheaterWinBookRecordForm(request.POST)  # PostForm으로 부터 받은 데이터를 처리하기 위한 인스턴스 생성
        if form.is_valid():  # 폼 검증 메소드
            print("this is post2")
            inputForm = form.save(commit=False)  # 오브젝트를 form으로 부터 가져오지만, 실제로 DB반영은 하지 않는다.
            # 가져 온 후 데이터 처리를 해도 된다.
            inputForm.user_name = request.user
            # inputForm 저장하기
            inputForm.save()
            # 저장한 후에 pk 값 가져오기
            print("this is after saving records pk :", inputForm.pk);
            new_winbook_pk = inputForm.pk
            messages.success(request, 'insert_success', extra_tags=new_winbook_pk)
            # 정보를 성공적으로 입력한 후에는, 메세지에 방금 입력된 pk값을 담아서 보내기
            print("this is post3")
            return redirect('winbook_list')
        else:
            print("this is post4")
            messages.error(request, "please enter right field");

    else:
        form = TheaterWinBookRecordForm()  # forms.py의 PostForm 클래스의 인스턴스
    return render(request, 'TheaterWinBook/winbook_insert.html', {'form': form})  # 템플릿 파일 경로 지정, 데이터 전달


@login_required(login_url='/login_view')
def winbook_statistics(request):
    # 로그인된 user를 확인하고
    login_user_name = request.user
    winbook_user_result = TheaterWinBookRecord.objects.filter(user_name=login_user_name).order_by('buy_date',
                                                                                                  '-pk')
    winbook_user_result_json = serializers.serialize('json', winbook_user_result)

    return render(request, 'TheaterWinBook/winbook_statistics.html',
                  {"winbook_user_result_json": winbook_user_result_json})


# 통계 페이지 기간 설정을 위한 AJAX
@login_required(login_url='/login_view')
def winbook_statistics_ajax(request):
    print("this is winbook_statistics_ajax:")
    datepicker_start = request.GET.get('datepicker_start', None)
    datepicker_end = request.GET.get('datepicker_end', None)
    print("this is datepicker_start:", datepicker_start, "and datepicker_end:", datepicker_end)
    # 기간안의 데이터를 DB에서 검색시작
    # 로그인된 user를 확인하고 해당 user 의 기록을 전부 가지고 오자.
    login_user_name = request.user
    winbook_user_result = TheaterWinBookRecord.objects.filter(user_name=login_user_name,
                                                              buy_date__range=[datepicker_start,
                                                                               datepicker_end]).order_by('buy_date',
                                                                                                         '-pk')
    winbook_user_result_json = serializers.serialize('json', winbook_user_result)
    print("this is json:" + winbook_user_result_json)

    data = {
        'winbook_user_result_json': winbook_user_result_json
    }
    print("this is send:", data)
    return JsonResponse(data)







def share_picks(request):
    pagenum = request.GET.get('pagenum', 1)
    # # GET 으로 받은 파라미터는 integer가 아니라, int 처리해줘야 한다....
    pagenum = int(pagenum)
    winbook_user_result = TheaterWinBookRecord.objects.filter(share_check=1).order_by('-writing_date','-pk')
    winbook_user_result_list = list(winbook_user_result)
    total_records_count = len(winbook_user_result_list)
     # 페이지 nator를 사용해서 10개씩 페이지로 만들기.
    paginator = Paginator(winbook_user_result, 10)
    print("this is paginator:", paginator)
    try:
        database_list_result_page = paginator.page(pagenum)
        database_list_result_page.page_range = paginator.page_range
        print("this is database_list_result_page page:", database_list_result_page.page_range)
        total_page_number = paginator.num_pages
        # 페이지에 보이는 페이지 numer의 수
        pagenum_in_per_page = int(3)
        start_page = ((pagenum - 1) // pagenum_in_per_page) * pagenum_in_per_page + 1
        end_page = start_page + pagenum_in_per_page
        if end_page > total_page_number:
            end_page = total_page_number + 1
        print("this is start_page:", start_page)
        database_list_result_page.start_page = int(start_page)
        database_list_result_page.end_page = int(end_page)
        print("this is end_page:", database_list_result_page.end_page)
        database_list_result_page.custom_page_range = range(database_list_result_page.start_page,
                                                            database_list_result_page.end_page)
        database_list_result_page.pagenum = pagenum
        database_list_result_page.total_page_number = total_page_number
    except PageNotAnInteger:
        print("this is not an integer")
        database_list_result_page = paginator.page(1)
    except Exception as e:
        print("this is page exception")
        # 에러가 나면 다시 1페이지로로 돌려주자.
        trace_back = traceback.format_exc()
        message = str(e) + " " + str(trace_back)
        return redirect('winbook_list')

    return render(request, 'TheaterWinBook/share_picks.html',
                  {"database_list_result_page": database_list_result_page, "total_records_count": total_records_count})



@login_required(login_url='/login_view')
def winbook_thumb_ajax(request):
    print("this is winbook_thumb_ajax:")
    thumb_style = request.POST.get('thumb_style', None)
    target_pk = request.POST.get('record_pk', None)
    print("this is target_pk:", target_pk)
    login_user_name = request.user
    thumb_result = 'thumb_fail'
    if thumb_style == 'up':
        target_record = TheaterWinBookRecord.objects.get(pk=target_pk)
        checkobject = TheaterWinBookRecordInfo.objects.filter(record_fk__pk=target_pk, by_whom=login_user_name,
                                                              record_thumbup=1)
        if not checkobject:
            #     추천한 기록이 없으면
            info_record = TheaterWinBookRecordInfo(record_fk=target_record, record_thumbup=1,
                                                          by_whom=login_user_name)
            info_record.save()
            thumb_result = "up_success"
        else:
            #     만약에 하나라도 있으면, 기존에 있던 추천을 취소하고삭제한다
            checkobject.delete()
            thumb_result = "up_cancel"

    if thumb_style == 'down':
        target_record = TheaterWinBookRecord.objects.get(pk=target_pk)
        checkobject = TheaterWinBookRecordInfo.objects.filter(record_fk__pk=target_pk, by_whom=login_user_name,
                                                              record_thumbdown=1)
        if not checkobject:
            #     추천한 기록이 없으면
            info_record = TheaterWinBookRecordInfo(record_fk=target_record, record_thumbdown=1,
                                                          by_whom=login_user_name)
            info_record.save()
            thumb_result = "down_success"
        else:
            #     만약에 하나라도 있으면, 기존에 있던 추천을 취소하고삭제한다
            checkobject.delete()
            thumb_result = "down_cancel"

    data = {
        'thumb_result': thumb_result
    }
    print("this is send:", data)
    return JsonResponse(data)

#  AJAX
@login_required(login_url='/login_view')
def winbook_reply_ajax(request):
    print("this is winbook_reply_ajax:")
    record_pk = request.POST.get('record_pk', None)
    print("question_pk", record_pk)
    content_reply = request.POST.get('content_reply', None)
    print("content_reply", content_reply)
    login_user_name = request.user
    target_record = TheaterWinBookRecord.objects.get(pk=record_pk)
    content_reply = TheaterWinBookRecordReply(record_fk=target_record, record_reply_content=content_reply,
                                            by_whom=login_user_name)
    content_reply.save()
    result = 'success'
    data = {
        'result': result
    }
    print("this is send:", data)
    return JsonResponse(data)


@login_required(login_url='/login_view')
def winbook_reply_delete(request):
    # request parameter 로 winbook.pk를 받아온다.
    record_pk = request.POST.get("record_pk", "")
    print("this is recordpk," + record_pk)
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = TheaterWinBookRecordReply.objects.get(pk=record_pk)
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    delete_success = "fail"
    if target_record.by_whom == login_user:
        print('this is login user');
        # pk번호를 기준으로 삭제. 삭제는 데이터를 지우는 것이 아니라, title 이랑 content를 수정하는 것으로 하자.
        target_record.record_reply_content = '-해당 댓글은 작성자에 의해 삭제되었습니다-'
        target_record.save()
        delete_success = "success";
    else:
        print("this is not equal login user")
    return HttpResponse(json.dumps({'delete_success': delete_success}), content_type="application/json")


@login_required(login_url='/login_view')
def winbook_reply_modify(request):
    # request parameter 로 winbook.pk를 받아온다.
    record_pk = request.POST.get("record_pk", "")
    print("this is get record_pk", record_pk)
    reply_modify_content = request.POST.get("reply_modify_content")
    print("this is recordpk," + record_pk)
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = TheaterWinBookRecordReply.objects.get(pk=record_pk)
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    delete_success = "fail"
    if target_record.by_whom == login_user:
        print('this is login user');
        # pk번호를 기준으로 삭제. 삭제는 데이터를 지우는 것이 아니라, title 이랑 content를 수정하는 것으로 하자.
        target_record.record_reply_content = reply_modify_content
        target_record.save()
        delete_success = "success";
    else:
        print("this is not equal login user")
    return HttpResponse(json.dumps({'delete_success': delete_success}), content_type="application/json")


