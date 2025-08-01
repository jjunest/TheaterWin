
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect


from ..forms import freeBoardForm, freeBoardForm
from ..models_freeboard import FreeBoard, FreeBoardInfo, FreeBoardReply
from django.contrib import messages
from django.db.models import F
from django.db.models import Max, Min
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page
import traceback
from django.shortcuts import render
from django.utils.safestring import mark_safe
import json



def freeBoard_list(request):
    pagenum = request.GET.get('pagenum', 1)
    # GET 으로 받은 파라미터는 integer가 아니라, int 처리해줘야 한다....
    pagenum = int(pagenum)
    print("this is pagenum", pagenum)
    database_list_result = FreeBoard.objects.order_by('-freeBoard_groupnum', 'freeBoard_sequencenum_ingroup')
    # 하나의 페이지당 들어갈 row 개수
    paginator = Paginator(database_list_result, 10)
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
        return redirect('freeBoard_list')
    return render(request, 'TheaterWinBook/freeBoard_list.html',
                  {"database_list_result_page": database_list_result_page})


@login_required(login_url='/login_view')
def freeBoard_write(request):
    print("this is freeboard write")
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = freeBoardForm(request.POST)  # PostForm으로 부터 받은 데이터를 처리하기 위한 인스턴스 생성
        is_original = request.POST.get('is_original')
        if is_original == 'freeBoard_original':
            # 새로운 글인지 확인)
            # 1. freeBoard record에서 가장 높은 pk를 구하고 그것을 +1 해준다.
            # 2-1. groupnm 에 넣어준다 (첫 글 생성일 경우)
            print("this is isoriginal test", is_original)
            if form.is_valid():  # 폼 검증 메소드
                # groupnum 을 pk 로 넣어준다.
                print("this is form is valid:", is_original)
                inputForm = form.save(commit=False)  # 오브젝트를 form으로 부터 가져오지만, 실제로 DB반영은 하지 않는다.
                # 가져 온 후 데이터 처리를 해도 된다.
                inputForm.user_name = request.user
                # inputForm.freeBoard_groupnum = 새로 쓴 원본 글이기 때문에 pk 를 groupnum 과 똑같이 해줌.
                if FreeBoard.objects.last() is None:
                    inputForm.freeBoard_groupnum = '1'
                else:
                    inputForm.freeBoard_groupnum = int(FreeBoard.objects.last().pk)
                print("inputForm.pk latest : ", inputForm.freeBoard_groupnum)
                # sequence num 을 넣어준다 = 1이다
                inputForm.freeBoard_sequencenum_ingroup = 1
                # level 을 넣어준다. 0이다.
                inputForm.freeBoard_level_ingroup = 0
                # 데이터베이스에 저장하기
                print("this is content:", inputForm.freeBoard_content)
                inputForm.save()
                freeBoard_fk = inputForm.pk
                freeBoard_record = FreeBoard.objects.get(pk=freeBoard_fk)
                freeBoard_info = FreeBoardInfo(freeBoard_fk=freeBoard_record)
                freeBoard_info.save()
                # freeBoard_info 로우를 만들어 준다.
                return redirect('freeBoard_list')
            else:
                errors = form.errors.as_data()
                for error in errors:
                    print('There was an error :', error)
                messages.error(request, "please enter right field")
        elif is_original == 'freeBoard_reply':
            print("this is freeBoard_reply")
            if form.is_valid():  # 폼 검증 메소드
                inputForm = form.save(commit=False)
                parent_freeBoard_pk = request.POST.get('freeBoard_pk')
                # 부모의 freeBoard_pk를 통해서 부모글의 정보를 가져온다.
                parent_freeBoard_record = FreeBoard.objects.get(pk=parent_freeBoard_pk)
                parent_freeBoard_groupnum = parent_freeBoard_record.freeBoard_groupnum
                parent_freeBoard_sequencenum_ingroup = parent_freeBoard_record.freeBoard_sequencenum_ingroup
                parent_freeBoard_level_ingroup = parent_freeBoard_record.freeBoard_level_ingorup

                print("this is freeBoard_record title:", parent_freeBoard_record)
                # groupnum 은 부모 글의 groupnum 과 같다
                # 2-2 해당 글이 댓글잉 경우
                # *공식
                # 1. SELECT NVL(MIN(SORTS),0) FROM BOARD
                #    WHERE  BGROUP = (원글의 BGROUP)
                #    AND SORTS > (원글의 SORTS)
                #    AND DEPTH <= (원글의 DEPTH)
                check = FreeBoard.objects.filter(freeBoard_groupnum=parent_freeBoard_groupnum,
                                                          freeBoard_sequencenum_ingroup__gt=parent_freeBoard_sequencenum_ingroup,
                                                          freeBoard_level_ingorup__lte=parent_freeBoard_level_ingroup).aggregate(
                    Min('freeBoard_sequencenum_ingroup'))["freeBoard_sequencenum_ingroup__min"]
                print("this is check:", check);
                # 2-1. 1번이 0 일 경우
                # 3. SELECT NVL(MAX(SORTS),0) + 1 FROM BOARD
                #     WHERE BGROUP = (원글의 BGROUP);
                # 4. INSERT INTO BOARD VALUES
                #    (번호, (원글의 BGROUP), (3번값), (원글의 DEPTH +1) ,' 제목')
                if check is None:
                    check = 0
                if check == 0:
                    new_sequencenum = FreeBoard.objects.filter(
                        freeBoard_groupnum=parent_freeBoard_groupnum).aggregate(Max('freeBoard_sequencenum_ingroup'))[
                        "freeBoard_sequencenum_ingroup__max"]
                    if new_sequencenum is None:
                        new_sequencenum = 0
                    new_sequencenum = new_sequencenum + 1
                    inputForm.freeBoard_groupnum = parent_freeBoard_groupnum
                    inputForm.freeBoard_sequencenum_ingroup = new_sequencenum
                    inputForm.freeBoard_level_ingorup = parent_freeBoard_level_ingroup + 1
                else:
                    # 2-2. 1번이 0이 아닐 경우
                    #
                    # 3. UPDATE BOARD SET SORTS = SORTS + 1
                    #   WHERE BGROUP =  (원글의 BGROUP)  AND SORTS >= (1번값)
                    FreeBoard.objects.filter(freeBoard_groupnum=parent_freeBoard_groupnum,
                                                      freeBoard_sequencenum_ingroup__gte=check).update(
                        freeBoard_sequencenum_ingroup=F('freeBoard_sequencenum_ingroup') + 1)

                    # 4. INSERT INTO BOARD VALUES
                    #    (번호, (원글의 BGROUP), (1번값), (원글의 DEPTH +1) ,' 제목')
                    inputForm.freeBoard_groupnum = parent_freeBoard_groupnum
                    inputForm.freeBoard_sequencenum_ingroup = check
                    inputForm.freeBoard_level_ingorup = parent_freeBoard_level_ingroup + 1

                # # 데이터베이스에 저장하기
                inputForm.save()
                return redirect('freeBoard_list')
            else:
                print("this is freeBoard_reply form is not valid")
                messages.error(request, "please enter right field")
    else:
        # 단순히 이동하는 작업이다.
        is_original = request.GET.get('is_original')
        if is_original == 'freeBoard_reply':
            # freeBoard_pk
            freeBoard_pk = request.GET.get('freeBoard_pk')
            print("this is freeBoard_pk:", freeBoard_pk)
            freeBoard_record = FreeBoard.objects.get(pk=freeBoard_pk)
            print("this is freeBoard_record title:", freeBoard_record.freeBoard_title)
            freeBoard_title = 'RE: ' + freeBoard_record.freeBoard_title
            form = freeBoardForm(initial={'freeBoard_title': freeBoard_title})  # forms.py의 PostForm 클래스의 인스턴스
        else:
            print("this is is_original is not reply_write")
            form = freeBoardForm()  # forms.py의 PostForm 클래스의 인스턴스
    return render(request, 'TheaterWinBook/freeBoard_write.html', {'form': form})  # 템플릿 파일 경로 지정, 데이터 전달





@login_required(login_url='/login_view')
def freeBoard_detail(request, freeBoard_pk):
    is_record_owner = 'not_owner'
    freeBoard_pk = freeBoard_pk
    # print("this is freeBoard_pk" + freeBoard_pk)
    target_record = FreeBoard.objects.get(pk=freeBoard_pk)
    # print("this is freeBoard_content : " + freeBoard_record.freeBoard_content)
    form = freeBoardForm(instance=target_record)  # forms.py의 PostForm 클래스의 인스턴스
    # 해당 글이 작성자 본인인지 확인 (본인이면 수정,삭제 버튼 누르자)
    login_user = request.user
    if target_record.user_name == login_user:
        is_record_owner = 'owner'
    target_record.freeBoard_hit = target_record.freeBoard_hit + 1
    target_record.save()

    # 추천과 비추천 숫자를 세자. FOREIGNER 외래키를 찾을 때에는 get이 아니라, filter 를 사용해야 한다.
    thumbup_count = FreeBoardInfo.objects.filter(freeBoard_fk=target_record, freeBoard_thumbup=1).count()
    thumbdown_count = FreeBoardInfo.objects.filter(freeBoard_fk=target_record, freeBoard_thumbdown=1).count()
    target_replys = FreeBoardReply.objects.filter(freeBoard_fk=target_record).order_by('reply_groupnum', 'reply_sequencenum_ingroup')
    return render(request, 'TheaterWinBook/freeBoard_detail.html',
                  {'freeBoard_record': target_record, 'form': form, 'is_record_owner': is_record_owner,
                   'thumbup_count': thumbup_count, 'thumbdown_count': thumbdown_count, 'target_replys': target_replys,
                   'login_user': login_user})

@login_required(login_url='/login_view')
def freeBoard_delete(request):
    # request parameter 로 winbook.pk를 받아온다.
    record_pk = request.POST.get("record_pk", "")
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = FreeBoard.objects.get(pk=record_pk)
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    delete_success = "fail"
    if target_record.user_name == login_user:
        print('this is login user');
        # pk번호를 기준으로 삭제. 삭제는 데이터를 지우는 것이 아니라, title 이랑 content를 수정하는 것으로 하자.
        target_record.freeBoard_title = '해당 글은 작성자에 의해 삭제되었습니다.'
        target_record.freeBoard_content = '- 해당 글은 작성자에 의해 삭제되었습니다 - '
        target_record.save()
        delete_success = "success";
    else:
        print("this is not equal login user")

    return HttpResponse(json.dumps({'delete_success': delete_success}), content_type="application/json")

    # 일치시에만 삭제 시작하고,

    # else 일치하지 않으면, 잘못된 접근 및 로그아웃 화면으로 넘기자.
#
#
@login_required(login_url='/login_view')
def freeBoard_modify(request):
    # user를 확인한다
    # 받은 pk로 글의 user를 확인한다.
    record_pk = request.GET.get("record_pk", "")
    login_user = request.user
    target_record = FreeBoard.objects.get(pk=record_pk)
    print("this is modify1")
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    if target_record.user_name == login_user:
        # 수정폼을 제출한 경우.
        print("this is modify2")
        if request.method == "POST":
            print("this is modify3")
            # create a form instance and populate it with data from the request:
            record_pk = request.POST.get("record_pk", "")
            target_modify_record = FreeBoard.objects.get(pk=record_pk)
            form = freeBoardForm(request.POST,
                                          instance=target_modify_record)  # PostForm으로 부터 받은 데이터를 처리하기 위한 인스턴스 생성
            print("this is modify4")
            if form.is_valid():  # 폼 검증 메소드
                print("this is modify5")
                inputForm = form.save(commit=False)  # 오브젝트를 form으로 부터 가져오지만, 실제로 DB반영은 하지 않는다.
                # 가져 온 후 데이터 처리를 ㅐㅎ도 된다.
                inputForm.user_name = request.user
                # inputForm 저장하기
                inputForm.save()
                # 저장한 후에 pk 값 가져오기
                print("this is after modifying records pk :", inputForm.pk)
                modify_winbook_pk = inputForm.pk
                messages.success(request, 'modify_success', extra_tags=modify_winbook_pk)
                # 정보를 성공적으로 입력한 후에는, 메세지에 방금 입력된 pk값을 담아서 보내기
                return redirect('freeBoard_detail', freeBoard_pk=modify_winbook_pk)
            else:
                messages.error(request, "please enter right field")
        else:
            #   정상적으로 modify로 이동시켜준다.
            form = freeBoardForm(instance=target_record)  # forms.py의 PostForm 클래스의 인스턴스
            return render(request, 'TheaterWinBook/freeBoard_modify.html',
                          {'form': form, 'record_pk': record_pk, 'target_record': target_record})
    else:
        #  유저가 확인이 안되면 에러 페이지로 넘김.
        return render(request, 'TheaterWinBook/error_wronguser.html')


# 본문의 댓글 쓰기
@login_required(login_url='/login_view')
def freeBoard_content_reply_write_ajax(request):
    print("this is freeBoard_content_reply_write_ajax:")
    freeBoard_pk = request.POST.get('freeBoard_pk', None)
    print("freeBoard_pk", freeBoard_pk)
    content_reply = request.POST.get('content_reply', None)
    print("content_reply", content_reply)
    login_user_name = request.user
    content_target = FreeBoard.objects.get(pk=freeBoard_pk)

    # groupnum, sequencenu,, levelnum
    if FreeBoardReply.objects.last() is None :
        reply_groupnum = 1
    else:
        reply_groupnum = int(FreeBoardReply.objects.last().pk)
    sequencenum_ingroup = 1
    level_ingroup = 0
    content_reply = FreeBoardReply(freeBoard_fk=content_target, freeBoard_reply_content=content_reply,
                                            by_whom=login_user_name, reply_groupnum = reply_groupnum,
                                            reply_sequencenum_ingroup = sequencenum_ingroup, reply_level_ingorup = level_ingroup)
    content_reply.save()
    result = 'success'
    data = {
        'result': result
    }
    print("this is send:", data)
    return JsonResponse(data)



@login_required(login_url='/login_view')
def freeBoard_reply_delete(request):
    # request parameter 로 winbook.pk를 받아온다.
    record_pk = request.POST.get("record_pk", "")
    print("this is recordpk," + record_pk)
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = FreeBoardReply.objects.get(pk=record_pk)
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    delete_success = "fail"
    if target_record.by_whom == login_user:
        print('this is login user');
        # pk번호를 기준으로 삭제. 삭제는 데이터를 지우는 것이 아니라, title 이랑 content를 수정하는 것으로 하자.
        target_record.freeBoard_reply_content = '-해당 댓글은 작성자에 의해 삭제되었습니다-'
        target_record.save()
        delete_success = "success";
    else:
        print("this is not equal login user")
    return HttpResponse(json.dumps({'delete_success': delete_success}), content_type="application/json")


@login_required(login_url='/login_view')
def freeBoard_reply_modify(request):
    # request parameter 로 winbook.pk를 받아온다.
    record_pk = request.POST.get("record_pk", "")
    print("this is get record_pk", record_pk)
    reply_modify_content = request.POST.get("reply_modify_content")
    print("this is recordpk," + record_pk)
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = FreeBoardReply.objects.get(pk=record_pk)
    # 글을 쓴 user와 로그인된 user가 일치하는지 확인
    delete_success = "fail"
    if target_record.by_whom == login_user:
        print('this is login user');
        # pk번호를 기준으로 삭제. 삭제는 데이터를 지우는 것이 아니라, title 이랑 content를 수정하는 것으로 하자.
        target_record.freeBoard_reply_content = reply_modify_content
        target_record.save()
        delete_success = "success";
    else:
        print("this is not equal login user")
    return HttpResponse(json.dumps({'delete_success': delete_success}), content_type="application/json")


@login_required(login_url='/login_view')
def freeBoard_re_reply_write_ajax(request):
    print("this is freeBoard_re_reply_write_ajax")
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        is_original = request.POST.get('is_original')
        re_reply_write_content = request.POST.get('re_reply_write_content')
        # 본 글의 pk를 의미함
        target_content_pk = request.POST.get('content_pk')
        print("this is target_content_pk:", target_content_pk)
        # 부모댓글의 pk를 의미함
        target_record_pk = request.POST.get('record_pk')
        print("this is record_pk:", target_record_pk)
        login_user_name = request.user
        if is_original == 're_reply':
            # 대댓글인 re_reply_write 는 무조건 부모 댓글이 존재하는 경우이다.
            print("this is question_re_reply_write_ajax")
            parent_reply_pk = request.POST.get('record_pk')
            # 부모의 question_pk를 통해서 부모글의 정보를 가져온다.
            parent_reply_record = FreeBoardReply.objects.get(pk=parent_reply_pk)
            parent_reply_groupnum = parent_reply_record.reply_groupnum
            parent_reply_sequencenum_ingroup = parent_reply_record.reply_sequencenum_ingroup
            parent_reply_level_ingroup = parent_reply_record.reply_level_ingorup
            # groupnum 은 부모 글의 groupnum 과 같다
            # 2-2 해당 글이 댓글잉 경우
            # *공식
            # 1. SELECT NVL(MIN(SORTS),0) FROM BOARD
            #    WHERE  BGROUP = (원글의 BGROUP)
            #    AND SORTS > (원글의 SORTS)
            #    AND DEPTH <= (원글의 DEPTH)
            check = FreeBoardReply.objects.filter(reply_groupnum=parent_reply_groupnum,
                                                          reply_sequencenum_ingroup__gt=parent_reply_sequencenum_ingroup,
                                                          reply_level_ingorup__lte=parent_reply_level_ingroup).aggregate(
                    Min('reply_sequencenum_ingroup'))["reply_sequencenum_ingroup__min"]
            print("this is check:", check);
            # 2-1. 1번이 0 일 경우
            # 3. SELECT NVL(MAX(SORTS),0) + 1 FROM BOARD
            #     WHERE BGROUP = (원글의 BGROUP);
            # 4. INSERT INTO BOARD VALUES
            #    (번호, (원글의 BGROUP), (3번값), (원글의 DEPTH +1) ,' 제목')
            if check is None:
                check = 0
            if check == 0:
                new_sequencenum = FreeBoardReply.objects.filter(
                    reply_groupnum=parent_reply_groupnum).aggregate(Max('reply_sequencenum_ingroup'))[
                    "reply_sequencenum_ingroup__max"]
                if new_sequencenum is None:
                    new_sequencenum = 0
                new_sequencenum = new_sequencenum + 1
                re_reply_groupnum = parent_reply_groupnum
                re_reply_sequencenum_ingroup = new_sequencenum
                re_reply_level_ingorup = parent_reply_level_ingroup + 1
            else:
                # 2-2. 1번이 0이 아닐 경우
                #
                # 3. UPDATE BOARD SET SORTS = SORTS + 1
                #   WHERE BGROUP =  (원글의 BGROUP)  AND SORTS >= (1번값)
                FreeBoardReply.objects.filter(reply_groupnum=parent_reply_groupnum,
                                                      reply_sequencenum_ingroup__gte=check).update(
                        reply_sequencenum_ingroup=F('reply_sequencenum_ingroup') + 1)

                # 4. INSERT INTO BOARD VALUES
                #    (번호, (원글의 BGROUP), (1번값), (원글의 DEPTH +1) ,' 제목')
                re_reply_groupnum = parent_reply_groupnum
                re_reply_sequencenum_ingroup = check
                re_reply_level_ingorup = parent_reply_level_ingroup + 1
            print("this is target_content_pk:", target_content_pk)
            print("this is by_whom:", login_user_name)
            print("this is re_reply reply_groupnum:", re_reply_groupnum)
            print("this is re_reply re_reply_sequencenum_ingroup:", re_reply_sequencenum_ingroup)
            print("this is re_reply reply_level_ingorup:", re_reply_level_ingorup)
            # # 데이터베이스에 저장하기
            content_target = FreeBoard.objects.get(pk=target_content_pk)
            re_reply = FreeBoardReply(freeBoard_fk=content_target,
                                                        freeBoard_reply_content=re_reply_write_content,
                                                        by_whom=login_user_name,
                                                        reply_groupnum= re_reply_groupnum,
                                                        reply_sequencenum_ingroup= re_reply_sequencenum_ingroup,
                                                        reply_level_ingorup= re_reply_level_ingorup)
            re_reply.save()
            result = 'success'
            data = {
                're_reply_write_success': result
            }
            print("this is send:", data)
            return JsonResponse(data)


# freeBoard 페이지의 thumb up & down 을 위한 AJAX
@login_required(login_url='/login_view')
def freeBoard_thumb_ajax(request):
    print("this is freeBoard_thumb_ajax:")
    thumb_style = request.POST.get('thumb_style', None)
    target_freeBoard_pk = request.POST.get('freeBoard_pk', None)
    print("this is target_pk:", target_freeBoard_pk)
    login_user_name = request.user
    thumb_result = 'thumb_fail'
    if thumb_style == 'up':
        target_freeBoard = FreeBoard.objects.get(pk=target_freeBoard_pk)
        checkobject = FreeBoardInfo.objects.filter(freeBoard_fk__pk=target_freeBoard_pk, by_whom=login_user_name,
                                                            freeBoard_thumbup=1)
        if not checkobject:
            #     추천한 기록이 없으면
            freeBoard_info_record = FreeBoardInfo(freeBoard_fk=target_freeBoard, freeBoard_thumbup=1,
                                                          by_whom=login_user_name)
            freeBoard_info_record.save()
            thumb_result = "up_success"
        else:
            #     만약에 하나라도 있으면, 기존에 있던 추천을 취소하고삭제한다
            checkobject.delete()
            thumb_result = "up_cancel"

    if thumb_style == 'down':
        target_freeBoard = FreeBoard.objects.get(pk=target_freeBoard_pk)
        checkobject = FreeBoardInfo.objects.filter(freeBoard_fk__pk=target_freeBoard_pk, by_whom=login_user_name,
                                                            freeBoard_thumbdown=1)
        if not checkobject:
            #     추천한 기록이 없으면
            freeBoard_info_record = FreeBoardInfo(freeBoard_fk=target_freeBoard, freeBoard_thumbdown=1,
                                                          by_whom=login_user_name)
            freeBoard_info_record.save()
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


@login_required(login_url='/login_view')
def freeBoard_usercheck(request):
    print("this is user_check")
    # request parameter 로 winbook.pk를 받아온다.
    record_pk = request.POST.get("record_pk", "")
    # 받은 pk로 글의 user를 확인한다.
    login_user = request.user
    target_record = FreeBoard.objects.get(pk=record_pk)
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