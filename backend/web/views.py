# backend/web/views.py
from datetime import date
import calendar
import json
import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from collections import defaultdict

from .forms import EmailUserCreationForm, UserUpdateForm
from .models import Category, MoneyFlow, User


MAX_EXPENSE_CATEGORIES = 16
MAX_INCOME_CATEGORIES = 8
CATEGORY_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
CATEGORY_ICON_KEYS = {
    "clothes",
    "daily",
    "default",
    "edit",
    "food",
    "fun",
    "home",
    "medical",
    "other_exp",
    "other_exp1",
    "other_inc",
    "plus",
    "salary",
    "transport",
    "utilities",
}
IMMUTABLE_CATEGORY_NAMES = {"支出その他", "収入その他", "その他"}


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
            user = form.save()
            login(request,user)
            # ログイン画面へリダイレクト

            return redirect("dashboard")
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
    today = date.today()

    # 月を前後にずらすための関数
    # 例：
    #   add_month(2026, 1, -1) → (2025, 12)
    #   add_month(2026, 12, 1) → (2027, 1)
    def add_month(y, m, delta):
        mm = m + delta
        yy = y + (mm - 1) // 12
        mm = (mm - 1) % 12 + 1
        return yy, mm

    # URLパラメータから年月を取得
    # /dashboard/?ym=2026-02 みたいな形式
    ym = request.GET.get("ym")

    # ymがあればそれを使う、なければ今月
    if ym:
        try:
            y_str, m_str = ym.split("-")
            year = int(y_str)
            month = int(m_str)
            # 月が1〜12以外ならエラー扱い
            if not (1 <= month <= 12):
                raise ValueError
        except Exception:
            # 変な値が来たら今月に戻す
            year, month = today.year, today.month
    else:
        # パラメータが無ければ今月
        year, month = today.year, today.month

		# weekday番号: 月=0, 火=1, 水=2, 木=3, 金=4, 土=5, 日=6
		# firstweekday=6 → 日曜始まり（[日,月,火,水,木,金,土]）
    cal = calendar.Calendar(firstweekday=6)

    dates = list(cal.itermonthdates(year, month))

		# date(2026,1,25), date(2026,1,26), date(2026,1,27), date(2026,1,28), ...）
    # datesを「7個ずつ」に区切りたい→range(0, len(dates), 7) → 0, 7, 14, 21, 28, ...となる
    # 1週目 dates[0:7]
    # 2週目 dates[7:14]
    # 3週目 dates[14:21]
    # weeks = [ 
    # [日, 月, 火, 水, 木, 金, 土],
    # [日, 月, 火, 水, 木, 金, 土],
    # ...]
    # weeks = [
		# [week0_day0, week0_day1, week0_day2, week0_day3, week0_day4, week0_day5, week0_day6],  # weeks[0]
		# [week1_day0, week1_day1, week1_day2, week1_day3, week1_day4, week1_day5, week1_day6],  # weeks[1]
	  # [week2_day0, week2_day1, week2_day2, week2_day3, week2_day4, week2_day5, week2_day6],  # weeks[2]
	  # [week3_day0, week3_day1, week3_day2, week3_day3, week3_day4, week3_day5, week3_day6],  # weeks[3]
    # ...]
    weeks = [dates[i:i + 7] for i in range(0, len(dates), 7)]

    # 前月・次月の年月を計算（ナビゲーション用）
    prev_y, prev_m = add_month(year, month, -1)
    next_y, next_m = add_month(year, month, 1)

    # 表示用ラベル（例: February, 2026）
    month_label = f"{calendar.month_name[month]}, {year}"

    # カレンダーに表示している最初と最後の日付
    # （前月・次月の分も含める）
    start_date = weeks[0][0]
    # 週の数が何個あるか分からないけど、一番最後の週[last_week_day0, last_week_day1, ..., last_week_day6]  # weeks[-1]
    end_date = weeks[-1][-1]

    # 表示範囲の日付だけを対象にする
    qs = (
        MoneyFlow.objects.select_related("category", "category__user")
        .filter(category__user=request.user, expense_date__range=(start_date, end_date))
    )

    # 日付ごとの「収入」「支出」をまとめる入れ物
    # 例: daily["2026-01-29"] = {"in": 5000, "out": 1200}
    daily = defaultdict(lambda: {"in": 0, "out": 0})

    for e in qs:
        # 日付を "YYYY-MM-DD" 形式の文字列にする
        key = e.expense_date.isoformat()

        # category.is_io_type が 1 なら収入、そうでなければ支出
        if e.category.is_in_type:
            daily[key]["in"] += int(e.amount)
        else:
            daily[key]["out"] += int(e.amount)


    # テンプレートで使いやすい形にデータを整形する
    # 1日分ごとに「辞書」を作って持たせる
    weeks_view = []
    for week in weeks:
        row = []
        for d in week:
            ds = d.isoformat()
            # その日の集計がなければ 0 円扱い
            t = daily.get(ds, {"in": 0, "out": 0})

            row.append({
                "date": d,                     # date型
                "ds": ds,                      # "YYYY-MM-DD"
                "day": d.day,                  # 日だけ（数字）
                "in_month": (d.month == month),# 今月かどうか
                "is_today": (d == today),      # 今日かどうか
                "in_total": t["in"],           # その日の収入合計
                "out_total": t["out"],         # その日の支出合計
            })
        weeks_view.append(row)

    # テンプレートにデータを渡して描画
    return render(
        request,
        "dashboard/calendar.html",
        {
            "weeks": weeks_view,                           # カレンダー本体
            "month": month,
            "month_label": month_label,                    # 表示ラベル
            "prev_ym": f"{prev_y:04d}-{prev_m:02d}",       # 前月リンク用（年4桁・月2桁ゼロ埋め）
            "next_ym": f"{next_y:04d}-{next_m:02d}",       # 次月リンク用（年4桁・月2桁ゼロ埋め）
            "today": today,
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
    def normalize_category(cat):
        # templateで安全に表示できる値だけを渡す
        icon_key = cat.icon_key if cat.icon_key in CATEGORY_ICON_KEYS else "default"
        color = cat.color if CATEGORY_COLOR_RE.match(cat.color or "") else "#999999"
        return {
            "id": cat.id,
            "name": cat.name,
            "icon_key": icon_key,
            "color": color,
            "is_builtin": bool(cat.is_builtin),
        }

    # ログイン中ユーザーに紐づくカテゴリ（個人＋同じグループ）を取得
    query = Q(user=request.user)
    if request.user.group_id:
        query |= Q(group_id=request.user.group_id)
    base_qs = Category.objects.filter(query).order_by("id")

    expense_categories_raw = base_qs.filter(is_in_type=False)
    income_categories_raw = base_qs.filter(is_in_type=True)

    expense_categories = [normalize_category(cat) for cat in expense_categories_raw]
    income_categories = [normalize_category(cat) for cat in income_categories_raw]

    expense_placeholders = range(max(0, MAX_EXPENSE_CATEGORIES - len(expense_categories)))
    income_placeholders = range(max(0, MAX_INCOME_CATEGORIES - len(income_categories)))

    return render(
        request,
        "dashboard/moneyflow/category.html",
        {
            "expense_categories": expense_categories,
            "income_categories": income_categories,
            "expense_placeholders": expense_placeholders,
            "income_placeholders": income_placeholders,
            "max_expense": MAX_EXPENSE_CATEGORIES,
            "max_income": MAX_INCOME_CATEGORIES,
        },
    )


def _category_query_for_user(user):
    query = Q(user=user)
    if user.group_id:
        query |= Q(group_id=user.group_id)
    return query


def _json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


@login_required(login_url="login")
@require_POST
@csrf_protect
def category_create_api(request):
    data = _json(request)
    name = (data.get("name") or "").strip()
    color = (data.get("color") or "#FF9400").strip()

    try:
        is_io_type = int(data.get("is_io_type"))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "is_io_type must be 0 or 1"}, status=400)

    if is_io_type not in (0, 1):
        return JsonResponse({"ok": False, "error": "is_io_type must be 0 or 1"}, status=400)
    if not name:
        return JsonResponse({"ok": False, "error": "name is required"}, status=400)
    if not CATEGORY_COLOR_RE.match(color):
        return JsonResponse({"ok": False, "error": "color must be #RRGGBB"}, status=400)

    is_in_type = bool(is_io_type)
    query = _category_query_for_user(request.user)

    limit = MAX_EXPENSE_CATEGORIES if is_io_type == 0 else MAX_INCOME_CATEGORIES
    current_count = Category.objects.filter(query, is_in_type=is_in_type).count()
    if current_count >= limit:
        return JsonResponse({"ok": False, "error": "これ以上カテゴリは追加できないよ"}, status=409)

    exists = Category.objects.filter(query, is_in_type=is_in_type, name=name).exists()
    if exists:
        return JsonResponse({"ok": False, "error": "同じ名前のカテゴリが既にあるよ"}, status=409)

    cat = Category.objects.create(
        user=request.user,
        group=request.user.group if request.user.group_id else None,
        name=name,
        color=color,
        is_in_type=is_in_type,
        icon_key="default",
        is_builtin=False,
    )
    return JsonResponse(
        {
            "ok": True,
            "category": {
                "id": cat.id,
                "name": cat.name,
                "color": cat.color,
                "is_io_type": is_io_type,
                "is_in_type": cat.is_in_type,
                "icon_key": cat.icon_key,
            },
        }
    )


@login_required(login_url="login")
@require_POST
@csrf_protect
def category_rename_api(request, category_id: int):
    data = _json(request)
    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "name is required"}, status=400)

    query = _category_query_for_user(request.user)
    try:
        cat = Category.objects.get(query, id=category_id)
    except Category.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    if cat.is_builtin or cat.name in IMMUTABLE_CATEGORY_NAMES:
        return JsonResponse({"ok": False, "error": "このカテゴリは変更できないよ"}, status=400)

    exists = (
        Category.objects.filter(query, is_in_type=cat.is_in_type, name=name)
        .exclude(id=cat.id)
        .exists()
    )
    if exists:
        return JsonResponse({"ok": False, "error": "同じ名前のカテゴリが既にあるよ"}, status=409)

    cat.name = name
    cat.save(update_fields=["name"])
    return JsonResponse({"ok": True, "category": {"id": cat.id, "name": cat.name}})


@login_required(login_url="login")
@require_POST
@csrf_protect
def category_delete_api(request, category_id: int):
    query = _category_query_for_user(request.user)
    try:
        cat = Category.objects.get(query, id=category_id)
    except Category.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    if cat.is_builtin or cat.name in IMMUTABLE_CATEGORY_NAMES:
        return JsonResponse({"ok": False, "error": "このカテゴリは削除できないよ"}, status=400)

    used = MoneyFlow.objects.filter(category_id=cat.id).exists()
    if used:
        return JsonResponse(
            {"ok": False, "error": "このカテゴリは既に記録に使われてるから削除できないよ"},
            status=409,
        )

    cat.delete()
    return JsonResponse({"ok": True, "deleted_id": category_id})


@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_moneyflow_edit_page(request):
    return render(request, "dashboard/moneyflow/moneyflow_edit.html")


@login_required(login_url="login")
@ensure_csrf_cookie
def charts_page(request):
    # ログイン中ユーザーに紐づく明細だけを新しい順で取得
    qs = (
        MoneyFlow.objects.select_related("category")
        .filter(category__user=request.user)
        .order_by("-expense_date", "-id")
    )

    # テンプレートで扱いやすいように一度リスト化
    expense_list = list(qs)

    # 画面表示名は「氏名 -> ユーザー名 -> メール」の優先で決める
    user_name = (
        request.user.get_full_name().strip()
        or request.user.username
        or request.user.email
    )

    # chart.html / charts.js で使うJSONデータを整形
    expense_data = [
        {
            "date": e.expense_date.isoformat(),  # "YYYY-MM-DD"
            "amount": e.amount,                  # 金額
            "category": e.category.name,         # カテゴリ名
            "categoryColor": e.category.color,   # カテゴリ色（#RRGGBB）
            "memo": e.memo,                      # メモ
            "user": user_name,                   # 表示用ユーザー名
        }
        for e in expense_list
    ]

    # チャート画面へデータを渡して描画
    return render(
        request,
        "dashboard/charts/chart.html",
        {"expense_data": expense_data, "user_name": user_name},
    )


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
