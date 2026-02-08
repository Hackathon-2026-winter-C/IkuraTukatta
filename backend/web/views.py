# backend/web/views.py
from datetime import date
import calendar

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from .forms import EmailUserCreationForm, UserUpdateForm
from .models import MoneyFlow, User


# /にアクセスがあった時
@ensure_csrf_cookie
def index_page(request):
    return redirect("login")


# サインアップ
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
    identifier = ""

    # POSTリクエスト（ログイン試行）
    if request.method == "POST":
        # フォームから email / password を取得
        raw_identifier = request.POST.get("email") or request.POST.get("username")
        identifier = (raw_identifier or "").strip()
        password = request.POST.get("password", "")
        # ログイン保持期間をユーザー選択で切り替えられる。
        remember_me = request.POST.get("remember_me") == "on"

        # 認証（emailをusernameとして使う）
        auth_identifier = identifier
        if identifier and "@" not in identifier:
            matched_user = User.objects.filter(username=identifier).only("email").first()
            if matched_user:
                auth_identifier = matched_user.email

        user = authenticate(request, username=auth_identifier, password=password)
        if user is not None:
            # 認証成功 → ログインしてdashboardへ
            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 14 if remember_me else 0)
            next_url = request.POST.get("next") or "dashboard"
            return redirect(next_url)

        # 認証失敗 → エラーメッセージをセット
        error = "メールアドレスかパスワードが違います。"

    context = {
        "error": error,
        "email": identifier,
        "next": request.GET.get("next", ""),
    }
    return render(request, "accounts/login.html", context)


#ログアウト処理
@require_GET
def logout_view(request):
    logout(request)
    return redirect("login")


# ログイン後表示されるカレンダーページ
@login_required(login_url="login")
def dashboard_page(request):
    moneyflows = (
        MoneyFlow.objects.select_related("category")
        .filter(category__user=request.user)
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


@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_list_page(request):
    return render(request, "dashboard/list/list.html")


@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_moneyflow_form_page(request):
    return render(request, "dashboard/moneyflow/moneyflow_form.html")


@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_moneyflow_category_page(request):
    return render(request, "dashboard/moneyflow/category.html")


@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_moneyflow_edit_page(request):
    return render(request, "dashboard/moneyflow/moneyflow_edit.html")


@login_required(login_url="login")
@ensure_csrf_cookie
def charts_page(request):
    return render(request, "dashboard/charts/chart.html")


@login_required(login_url="login")
@ensure_csrf_cookie
def account_page(request):
    return render(request, "accounts/account.html")


@login_required(login_url="login")
def account_edit(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("account")
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, "accounts/account_edit.html", {"form": form})


@login_required(login_url="login")
@require_GET
def users_api(request):
    users = list(User.objects.values("id", "username", "email"))
    return JsonResponse({"users": users})


# サインアップ
# def signup(request):
#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect("login") # 登録後ログインページへ
#
#     else:
#         form = UserCreationForm()
#     return render(request, "signup.html", {"form": form})
