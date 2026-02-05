# backend/web/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,authenticate,logout
from .forms import EmailUserCreationForm
from .models import MoneyFlow ,User

from datetime import date
import calendar


# /にアクセスがあった時
@ensure_csrf_cookie
def index_page(request):
    return redirect("login")


# サインアップ
@csrf_exempt
@ensure_csrf_cookie
def signup_page(request):
    # POSTリクエスト
    if request.method == "POST":
        form = EmailUserCreationForm(request.POST)
        # バリデーションOKならユーザー作成
        if form.is_valid():
            form.save()
            # ログイン画面へリダイレクト
            return redirect("login")
    # GETリクエスト
    else:
        form = EmailUserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})


# ログイン
@ensure_csrf_cookie
def login_page(request):
    # GETリクエスト
    # すでにログイン済みなら dashboard へ
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    email = ""

    # POSTリクエスト（ログイン試行）
    if request.method == "POST":
        # フォームから email / password を取得
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        # 認証（emailをusernameとして使う）
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # 認証成功 → ログインしてdashboardへ
            login(request, user)
            return redirect("dashboard")
        # 認証失敗 → エラーメッセージをセット
        error = "メールアドレスかパスワードが違います。"
    return render(request, 'accounts/login.html',{"error": error, "email": email})

#ログアウト処理
@require_GET
def logout_view(request):
    logout(request)
    return redirect("login")


# ログイン後表示されるカレンダーページ
@login_required(login_url="login")
def dashboard_page(request):
    user = User.objects.filter(email=request.user.email).first()
    if user is None:
        return redirect("login")

    moneyflows = (
        MoneyFlow.objects.select_related("category")
        .filter(category__user=user)
        .order_by("-expense_date", "-id")
    )

    today = date.today()
    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(today.year, today.month)
    month_label = f"{today.year}年{today.month}月"

    return render(
        request,
        "dashboard/calendar.html",
        {
            "month_label": month_label,
            "weeks": weeks,
            "today_day": today.day,
            "moneyflows": moneyflows,
        },
    )
    return render (request, "dashboard/calendar.html")


@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_list_page(request):
    return render(request, 'dashboard/list/list.html')

@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_moneyflow_form_page(request):
    return render(request, 'dashboard/moneyflow/moneyflow_form.html')

@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_moneyflow_category_page(request):
    return render(request, 'dashboard/moneyflow/category.html')

@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_moneyflow_edit_page(request):
    return render(request, 'dashboard/moneyflow/moneyflow_edit.html')

@login_required(login_url="login")
@ensure_csrf_cookie
def charts_page(request):
    return render (request, 'dashboard/charts/chart.html')

@login_required(login_url="login")
@ensure_csrf_cookie
def account_page(request):
    return render(request, 'accounts/account.html')

# サインアップ
# def signup(request):
#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect("login") # 登録後ログインページへ
    
#     else:
#         form = UserCreationForm()
#     return render(request, "signup.html", {"form": form})
