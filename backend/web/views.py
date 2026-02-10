# backend/web/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,authenticate,logout
from .forms import EmailUserCreationForm
from .models import User, Category, MoneyFlow
from collections import defaultdict # これを追加！
from datetime import date # これも追加！

from datetime import date
import calendar


@ensure_csrf_cookie
def index_page(request):
    return render(request, "index.html")


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

@require_GET
def logout_view(request):
    logout(request)
    return redirect("login")


# ログイン後表示されるカレンダーページ
@login_required(login_url="login")
def dashboard_page(request):
    return render (request, "dashboard/calendar.html")


@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_list_page(request):
    user_email = "demo@example.com" # または request.user.email
    qs = (
        MoneyFlow.objects.select_related("category__user", "category")
        .filter(category__user__email=user_email)
        .order_by("-expense_date", "-id")
    )   
    # 日付ごとに支出をグループ化する
    grouped_expenses = defaultdict(list)
    for e in qs:
        grouped_expenses[e.expense_date].append({
            "amount": e.amount,
            "category": e.category.name,
            "categoryColor": e.category.color,
            "memo": e.memo,
            "user": e.category.user.username,
        })
    # 日付の新しい順にソートされたリストにする
    sorted_grouped_expenses = sorted(grouped_expenses.items(), key=lambda item: item[0], reverse=True)
    # user_name を準備
    user_name = request.user.username if request.user.username else user_email
    return render(
        request,
        'dashboard/list/list.html',
        {"grouped_expenses": sorted_grouped_expenses, "user_name": user_name} # ここで渡すデータを変更！
    )

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
    user_email = "demo@example.com" # ここを "demo@example.com" に固定！
    qs = (
        MoneyFlow.objects.select_related("category__user", "category")
        .filter(category__user__email=user_email)
        .order_by("-expense_date", "-id")
    )
    expense_list = list(qs)
    user_name = "demo" # user_name も "demo" に固定する
    expense_data = [
        {
            "date": e.expense_date.isoformat(),
            "amount": e.amount,
            "category": e.category.name,
            "categoryColor": e.category.color,
            "memo": e.memo,
            "user": e.category.user.username,
        }
        for e in expense_list
    ]
    return render (
        request,
        'dashboard/charts/chart.html',
        {"expense_data": expense_data, "user_name": user_name}
    )
    

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
