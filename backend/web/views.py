# backend/web/views.py
from datetime import date
import calendar
import json
import re
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from botocore.exceptions import BotoCoreError, ClientError
from PIL import UnidentifiedImageError

from .profile_image_service import save_profile_image
from .forms import EmailUserCreationForm, UserUpdateForm
from .models import Category, MoneyFlow, User, LedgerShare
from .ledger_utils import get_ledger_owner, can_view, SESSION_KEY


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
    return render(request, "accounts/darkmode-modal.html", {})


# サインアップ
@ensure_csrf_cookie
def signup_page(request):
    if request.method == "POST":
        form = EmailUserCreationForm(request.POST)
        profile_image = request.FILES.get("profile_image")

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()

                    if profile_image:
                        key = save_profile_image(user.id, profile_image)
                        base_url = settings.AWS_S3_BASE_URL or (
                            f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"
                        )
                        user.image_url = f"{base_url.rstrip('/')}/{key.lstrip('/')}"
                        user.save(update_fields=["image_url"])

            except (BotoCoreError, ClientError, OSError, UnidentifiedImageError):
                form.add_error(None, "プロフィール画像の保存に失敗しました。時間をおいて再度お試しください。")
            else:
                login(request, user)
                return redirect("dashboard")
    else:
        form = EmailUserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})


# ログイン
@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    identifier = ""

    if request.method == "POST":
        raw_identifier = request.POST.get("email") or request.POST.get("username")
        identifier = (raw_identifier or "").strip()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me") == "on"

        auth_identifier = identifier
        if identifier and "@" not in identifier:
            matched_user = User.objects.filter(username=identifier).only("email").first()
            if matched_user:
                auth_identifier = matched_user.email

        user = authenticate(request, username=auth_identifier, password=password)
        if user is not None:
            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 14 if remember_me else 0)
            next_url = request.POST.get("next") or "dashboard"
            return redirect(next_url)

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


# ログイン後表示されるカレンダーページ（共有対象）
@login_required(login_url="login")
def dashboard_page(request):
    today = date.today()

    def add_month(y, m, delta):
        mm = m + delta
        yy = y + (mm - 1) // 12
        mm = (mm - 1) % 12 + 1
        return yy, mm

    ym = request.GET.get("ym")

    if ym:
        try:
            y_str, m_str = ym.split("-")
            year = int(y_str)
            month = int(m_str)
            if not (1 <= month <= 12):
                raise ValueError
        except Exception:
            year, month = today.year, today.month
    else:
        year, month = today.year, today.month

    cal = calendar.Calendar(firstweekday=6)
    dates = list(cal.itermonthdates(year, month))
    weeks = [dates[i:i + 7] for i in range(0, len(dates), 7)]

    prev_y, prev_m = add_month(year, month, -1)
    next_y, next_m = add_month(year, month, 1)

    month_label = f"{calendar.month_name[month]}, {year}"

    start_date = weeks[0][0]
    end_date = weeks[-1][-1]

    # ★共有対応：閲覧中の家計簿オーナーで絞る
    ledger_owner = get_ledger_owner(request)

    qs = (
        MoneyFlow.objects.select_related("category", "category__user")
        .filter(category__user=ledger_owner, expense_date__range=(start_date, end_date))
    )

    daily = defaultdict(lambda: {"in": 0, "out": 0})
    for e in qs:
        key = e.expense_date.isoformat()
        if e.category.is_in_type:
            daily[key]["in"] += int(e.amount)
        else:
            daily[key]["out"] += int(e.amount)

    weeks_view = []
    for week in weeks:
        row = []
        for d in week:
            ds = d.isoformat()
            t = daily.get(ds, {"in": 0, "out": 0})
            row.append({
                "date": d,
                "ds": ds,
                "day": d.day,
                "in_month": (d.month == month),
                "is_today": (d == today),
                "in_total": t["in"],
                "out_total": t["out"],
            })
        weeks_view.append(row)

    user_name = (
        ledger_owner.get_full_name().strip()
        or ledger_owner.username
        or ledger_owner.email
    )
    is_owner_view = (ledger_owner.id == request.user.id)

    return render(
        request,
        "dashboard/calendar.html",
        {
            "weeks": weeks_view,
            "month": month,
            "month_label": month_label,
            "prev_ym": f"{prev_y:04d}-{prev_m:02d}",
            "next_ym": f"{next_y:04d}-{next_m:02d}",
            "today": today,
            "user_name": user_name,
            "ledger_owner": ledger_owner,
            "is_owner_view": is_owner_view,
        },
    )


# 支出リスト（共有対象）
@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_list_page(request):
    ledger_owner = get_ledger_owner(request)

    qs = (
        MoneyFlow.objects.select_related("category__user", "category")
        .filter(category__user=ledger_owner)
        .order_by("-expense_date", "-id")
    )

    grouped_expenses = defaultdict(list)
    for e in qs:
        grouped_expenses[e.expense_date].append({
            "id": e.id,
            "amount": e.amount,
            "amount_sign": "+" if e.category.is_in_type else "-",
            "mode": "income" if e.category.is_in_type else "expense",
            "category": e.category.name,
            "categoryColor": e.category.color,
            "icon_key": e.category.icon_key,
            "memo": e.memo,
            "user": e.category.user.username,
        })

    sorted_grouped_expenses = sorted(grouped_expenses.items(), key=lambda item: item[0], reverse=True)

    user_name = (
        ledger_owner.get_full_name().strip()
        or ledger_owner.username
        or ledger_owner.email
    )
    is_owner_view = (ledger_owner.id == request.user.id)

    return render(
        request,
        "dashboard/list/list.html",
        {
            "grouped_expenses": sorted_grouped_expenses,
            "user_name": user_name,
            "ledger_owner": ledger_owner,
            "is_owner_view": is_owner_view,
        },
    )


# 収支入力（共有対象外：今まで通り自分だけ）
@login_required(login_url="login")
def dashboard_moneyflow_form_page(request):
    mode = (request.GET.get("mode") or "expense").strip()
    if mode not in ("expense", "income", "receipt"):
        mode = "expense"

    query = _category_query_for_user(request.user)

    def normalize_category(cat: Category):
        icon_key = cat.icon_key if cat.icon_key in CATEGORY_ICON_KEYS else "default"
        color = cat.color if CATEGORY_COLOR_RE.match(cat.color or "") else "#999999"
        return {
            "id": cat.id,
            "name": cat.name,
            "icon_key": icon_key,
            "color": color,
            "is_in_type": bool(cat.is_in_type),
            "is_builtin": bool(cat.is_builtin),
        }

    categories = []
    if mode in ("expense", "income"):
        is_in_type = (mode == "income")
        qs = Category.objects.filter(query, is_in_type=is_in_type).order_by("id")
        categories = [normalize_category(cat) for cat in qs]

    if request.method == "POST":
        if mode == "receipt":
            return JsonResponse({"ok": False, "error": "receiptはまだ未実装だよ"}, status=400)

        amount_raw = (request.POST.get("amount") or "").strip()
        title = (request.POST.get("title") or "").strip()
        expense_date = (request.POST.get("expense_date") or "").strip()
        category_id_raw = (request.POST.get("category_id") or "").strip()

        amount_raw = amount_raw.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        amount_digits = re.sub(r"[^\d]", "", amount_raw)

        try:
            amount = int(amount_digits)
            category_id = int(category_id_raw)
        except Exception:
            return JsonResponse({"ok": False, "error": "金額/カテゴリが不正だよ"}, status=400)

        if amount <= 0:
            return JsonResponse({"ok": False, "error": "金額は1円以上にしてね"}, status=400)
        if not expense_date:
            return JsonResponse({"ok": False, "error": "日付を入れてね"}, status=400)

        try:
            cat = Category.objects.get(query, id=category_id)
        except Category.DoesNotExist:
            return JsonResponse({"ok": False, "error": "カテゴリが見つからないよ"}, status=404)

        if mode == "expense" and cat.is_in_type:
            return JsonResponse({"ok": False, "error": "支出タブでは収入カテゴリは選べないよ"}, status=400)
        if mode == "income" and (not cat.is_in_type):
            return JsonResponse({"ok": False, "error": "収入タブでは支出カテゴリは選べないよ"}, status=400)

        created = MoneyFlow.objects.create(
            category=cat,
            amount=amount,
            expense_date=expense_date,
            memo=title,
        )
        return redirect(f"{redirect('dashboard_list').url}?focus={created.id}")

    user_name = (
        request.user.get_full_name().strip()
        or request.user.username
        or request.user.email
    )
    return render(
        request,
        "dashboard/moneyflow/moneyflow_form.html",
        {
            "today": date.today().isoformat(),
            "categories": categories,
            "mode_expense": (mode == "expense"),
            "mode_income": (mode == "income"),
            "mode_receipt": (mode == "receipt"),
            "user_name": user_name,
        },
    )


@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_moneyflow_category_page(request):
    def normalize_category(cat):
        icon_key = cat.icon_key if cat.icon_key in CATEGORY_ICON_KEYS else "default"
        color = cat.color if CATEGORY_COLOR_RE.match(cat.color or "") else "#999999"
        return {
            "id": cat.id,
            "name": cat.name,
            "icon_key": icon_key,
            "color": color,
            "is_builtin": bool(cat.is_builtin),
        }

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
    entry_id = (request.GET.get("id") or "").strip()
    if not entry_id.isdigit():
        return redirect("dashboard_moneyflow_form")

    entry = get_object_or_404(
        MoneyFlow.objects.select_related("category"),
        id=int(entry_id),
        category__user=request.user,
    )

    mode = (request.GET.get("mode") or request.POST.get("mode") or "").strip()
    if mode not in ("expense", "income", "receipt"):
        mode = "income" if entry.category.is_in_type else "expense"

    query = _category_query_for_user(request.user)

    def normalize_category(cat: Category):
        icon_key = cat.icon_key if cat.icon_key in CATEGORY_ICON_KEYS else "default"
        color = cat.color if CATEGORY_COLOR_RE.match(cat.color or "") else "#999999"
        return {
            "id": cat.id,
            "name": cat.name,
            "icon_key": icon_key,
            "color": color,
            "is_in_type": bool(cat.is_in_type),
            "is_builtin": bool(cat.is_builtin),
        }

    categories = []
    if mode in ("expense", "income"):
        is_in_type = (mode == "income")
        qs = Category.objects.filter(query, is_in_type=is_in_type).order_by("id")
        categories = [normalize_category(cat) for cat in qs]

    if request.method == "POST":
        if mode == "receipt":
            return JsonResponse({"ok": False, "error": "receiptはまだ未実装だよ"}, status=400)

        amount_raw = (request.POST.get("amount") or "").strip()
        title = (request.POST.get("title") or "").strip()
        expense_date = (request.POST.get("expense_date") or "").strip()
        category_id_raw = (request.POST.get("category_id") or "").strip()

        amount_raw = amount_raw.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        amount_digits = re.sub(r"[^\d]", "", amount_raw)

        try:
            amount = int(amount_digits)
            category_id = int(category_id_raw)
        except Exception:
            return JsonResponse({"ok": False, "error": "金額/カテゴリが不正だよ"}, status=400)

        if amount <= 0:
            return JsonResponse({"ok": False, "error": "金額は1円以上にしてね"}, status=400)
        if not expense_date:
            return JsonResponse({"ok": False, "error": "日付を入れてね"}, status=400)

        try:
            cat = Category.objects.get(query, id=category_id)
        except Category.DoesNotExist:
            return JsonResponse({"ok": False, "error": "カテゴリが見つからないよ"}, status=404)

        if mode == "expense" and cat.is_in_type:
            return JsonResponse({"ok": False, "error": "支出タブでは収入カテゴリは選べないよ"}, status=400)
        if mode == "income" and (not cat.is_in_type):
            return JsonResponse({"ok": False, "error": "収入タブでは支出カテゴリは選べないよ"}, status=400)

        entry.category = cat
        entry.amount = amount
        entry.expense_date = expense_date
        entry.memo = title
        entry.save(update_fields=["category", "amount", "expense_date", "memo"])

        return redirect(f"{redirect('dashboard_list').url}?focus={entry.id}")

    user_name = (
        request.user.get_full_name().strip()
        or request.user.username
        or request.user.email
    )

    return render(
        request,
        "dashboard/moneyflow/moneyflow_form.html",
        {
            "entry": entry,
            "today": date.today().isoformat(),
            "categories": categories,
            "mode_expense": (mode == "expense"),
            "mode_income": (mode == "income"),
            "mode_receipt": (mode == "receipt"),
            "user_name": user_name,
        },
    )


@login_required(login_url="login")
@require_POST
@csrf_protect
def dashboard_moneyflow_delete_page(request):
    entry_id = (request.GET.get("id") or "").strip()
    if not entry_id.isdigit():
        return redirect("dashboard_list")

    entry = get_object_or_404(
        MoneyFlow,
        id=int(entry_id),
        category__user=request.user,
    )
    entry.delete()
    return redirect("dashboard_list")


# 円グラフ（共有対象）
@login_required(login_url="login")
@ensure_csrf_cookie
def charts_page(request):
    ledger_owner = get_ledger_owner(request)

    qs = (
        MoneyFlow.objects.select_related("category")
        .filter(category__user=ledger_owner)
        .order_by("-expense_date", "-id")
    )

    expense_list = list(qs)

    user_name = (
        ledger_owner.get_full_name().strip()
        or ledger_owner.username
        or ledger_owner.email
    )
    is_owner_view = (ledger_owner.id == request.user.id)

    expense_data = [
        {
            "date": e.expense_date.isoformat(),
            "amount": e.amount,
            "category": e.category.name,
            "categoryColor": e.category.color,
            "memo": e.memo,
            "user": user_name,
        }
        for e in expense_list
    ]

    return render(
        request,
        "dashboard/charts/chart.html",
        {
            "expense_data": expense_data,
            "user_name": user_name,
            "ledger_owner": ledger_owner,
            "is_owner_view": is_owner_view,
        },
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


# ===== 共有: 閲覧先切り替えAPI =====
@login_required(login_url="login")
@require_POST
@csrf_protect
def ledger_select_api(request):
    data = _json(request)
    try:
        owner_id = int(data.get("owner_id"))
    except Exception:
        return JsonResponse({"ok": False, "error": "bad_request"}, status=400)

    if not can_view(owner_id, request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    request.session[SESSION_KEY] = owner_id
    return JsonResponse({"ok": True, "owner_id": owner_id})


# ===== 共有: メールで閲覧者を追加 =====
@login_required(login_url="login")
@require_POST
@csrf_protect
def ledger_share_add_api(request):
    data = _json(request)
    email = (data.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"ok": False, "error": "email is required"}, status=400)

    viewer = User.objects.filter(email__iexact=email).first()
    if not viewer:
        return JsonResponse({"ok": False, "error": "user_not_found"}, status=404)

    if viewer.id == request.user.id:
        return JsonResponse({"ok": False, "error": "cannot_share_to_self"}, status=400)

    obj, created = LedgerShare.objects.get_or_create(owner=request.user, viewer=viewer)
    return JsonResponse(
        {
            "ok": True,
            "created": created,
            "viewer": {"id": viewer.id, "email": viewer.email, "username": viewer.username},
        }
    )


# ===== 共有: 自分が共有している閲覧者一覧 =====
@login_required(login_url="login")
@require_GET
def ledger_share_list_api(request):
    qs = LedgerShare.objects.select_related("viewer").filter(owner=request.user).order_by("viewer__email")
    viewers = [{"id": s.viewer.id, "email": s.viewer.email, "username": s.viewer.username} for s in qs]
    return JsonResponse({"ok": True, "viewers": viewers})


# ===== 共有: 閲覧者を削除 =====
@login_required(login_url="login")
@require_POST
@csrf_protect
def ledger_share_remove_api(request):
    data = _json(request)
    try:
        viewer_id = int(data.get("viewer_id"))
    except Exception:
        return JsonResponse({"ok": False, "error": "bad_request"}, status=400)

    deleted, _ = LedgerShare.objects.filter(owner=request.user, viewer_id=viewer_id).delete()
    return JsonResponse({"ok": True, "deleted": bool(deleted)})

@login_required(login_url="login")
@require_GET
def ledger_available_api(request):
    """
    自分が「閲覧できる家計簿の一覧（owner一覧）」を返す
    - 自分自身
    - 自分がviewerとして共有されている owner
    ついでに、現在選択中(owner_id)も返す
    """
    viewer = request.user

    # viewerとして共有されている owner を取得
    shares = (
        LedgerShare.objects.select_related("owner")
        .filter(viewer=viewer)
        .order_by("owner__email")
    )

    owners = []
    # まず自分
    owners.append(
        {
            "id": viewer.id,
            "email": viewer.email,
            "username": viewer.username,
        }
    )

    # 共有されている人（owner）
    for s in shares:
        o = s.owner
        if not o:
            continue
        # 念のため権限チェック（基本trueになるはず）
        if not can_view(o.id, viewer):
            continue
        owners.append(
            {
                "id": o.id,
                "email": o.email,
                "username": o.username,
            }
        )

    # 現在の選択中owner
    current_owner = get_ledger_owner(request)

    return JsonResponse(
        {
            "ok": True,
            "current_owner_id": current_owner.id,
            "owners": owners,
        }
    )
