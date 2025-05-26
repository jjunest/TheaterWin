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
from django.utils.encoding import smart_str
# from django.utils.encoding import smart_text

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


# # Create your views here.
# def post_list(request):
#     posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
#     return render(request, 'TheaterWinBook/post_list.html', {'posts': posts})
#
#



def index_real(request):
    return render(request, 'TheaterWinBook/index.html')


def error_404(request):
    return render(request, 'TheaterWinBook/error_404.html')


def bower_test(request):
    return render(request, 'TheaterWinBook/bower_test.html')


def calendar_test(request):
    return render(request, 'TheaterWinBook/calendar_test.html')


def error_wronguser(request):
    return render(request, 'TheaterWinBook/error_wronguser.html')


# is_authenticated 역할이 안되기 때문에 (필드로 변경되었기 대문에), 해당 메소드를 넣어서 wrapper method 로 사용.
def is_authenticated(user):
    if callable(user.is_authenticated):
        return user.is_authenticated()
    return user.is_authenticated


def index(request):
    # print("this is index")
    # return render(request, 'index.html')

    if is_authenticated(request.user):
        return redirect('stock_rank')
        # return redirect('winbook_insert')
    else:
        return redirect('index_real')
        # return render(request, 'TheaterWinBook/index.html')


def index_real(request):
    return render(request, 'TheaterWinBook/index.html')


def index_video_test(request):
    return render(request, 'TheaterWinBook/index_video_test.html')


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'TheaterWinBook/post_detail.html', {'post': post})




def appchat(request):
    return render(request, 'TheaterWinBook/appchat.html', {})



def to_winnerBros(request):
    return render(request, 'TheaterWinBook/to_winnerBros.html')


def signup(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        print('post')
        if form.is_valid():
            # 회원가입 정보를 이용하여 새로운 사용자 만들기.
            print('valid1')
            new_user = User.objects.create_user(**form.cleaned_data)
            # 회원가입을 하고 로그인을 바로 하는 것이 아니라, 로그인 페이지로 이동시키자
            # login(request, new_user)
            print('valid2')
            messages.success(request, "회원가입 완료! 가입하신 정보로 로그인해주세요!")
            return redirect('login_view')
            # signup_try = 'signup_success'
            # return render(request, 'TheaterWinBook/login_view.html', {'signup_try': signup_try})
        else:
            form = UserForm()
            # 검증에 실패시 form.error 에 오류 정보를 저장하여 함께 렌더링

            return render(request, 'TheaterWinBook/signup.html', {'form': form})

    else:
        print('signup_else part')
        form = UserForm()
        return render(request, 'TheaterWinBook/signup.html', {'form': form})


def login_view(request):
    next = request.GET.get('next', '/')
    print('this is next:', next);
    # 만약 nextpage 가 /login_view/라면 index페이지로 넘기자
    if (next == '/login_view/'):
        next = '/index'
    if (next == '/' or next == '/index/'):
        auth_page = 'no'
    else:
        auth_page = 'yes'
    if request.method == "POST":
        form = LoginForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(next)


        else:
            login_try = 'login_fail'
            return render(request, 'TheaterWinBook/login_view.html',
                          {'form': form, 'login_try': login_try, 'auth_page': auth_page})
    else:
        form = LoginForm()
        return render(request, 'TheaterWinBook/login_view.html', {'form': form, 'auth_page': auth_page})

#
# def logout_view(request):
#     logout(request)
#     return redirect('index')
#
#
# 아이디 중복 체크를 위한 AJAX
def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    print("this is is_taken:", data)
    return JsonResponse(data)


# 아이디 중복 체크를 위한 AJAX
def kakaoapi_test(request):
    return render(request, 'TheaterWinBook/kakaoapi_test.html')




# CHANNELS 를 이용한 CHATTING 채팅 시작
def full_chatting(request):
    return render(request, 'TheaterWinBook/full_chatting.html')


def chatting_room(request, room_name):
    return render(request, 'TheaterWinBook/chatting_room.html', {
        'room_name_json': mark_safe(json.dumps(room_name))
    })


def template_content_52(request):
    return render(request, 'TheaterWinBook/template_content_52.html')