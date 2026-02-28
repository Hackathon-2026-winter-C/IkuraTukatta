# backend/web/views.py
from datetime import date
import calendar
import json
import re
import logging
from collections import defaultdict

from django.urls import reverse
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from botocore.exceptions import BotoCoreError, ClientError
from PIL import UnidentifiedImageError

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .profile_image_service import save_profile_image
from .forms import EmailUserCreationForm, UserUpdateForm
from .category_defaults import create_default_categories
from .models import Category, MoneyFlow, User, ShareGroup, ShareGroupMember
from .receipt_image_service import compress_and_resize_receipt
from .receipt_bedrock_service import analyze_receipt_with_bedrock

from .ledger_utils import (
    GROUP_SESSION_KEY,
    get_current_group_id,
    get_scope_user_ids,
    can_use_group,
)

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
logger = logging.getLogger(__name__)

@login_required(login_url="login")
@require_POST
@csrf_protect
def account_delete_api(request):
    user = request.user
    ShareGroup.objects.filter(created_by_user=user).delete()
    user.delete()
    logout(request)
    return JsonResponse({"ok": True})


def _json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


# /にアクセスがあった時
@ensure_csrf_cookie
def index_page(request):
    return redirect("login")

#エラーページ（403)
def error_403(request,exception):
    return render(request,"accounts/error-page403.html",status=403)

#エラーページ（404)
def error_404(request,exception):
    return render(request,"accounts/error-page404.html",status=404)

#エラーページ（500)
def error_500(request):
    return render(request,"accounts/error-page500.html",status=500)

def _username_from_google_profile(email: str, google_name: str = "") -> str:
    """
    Googleログインで新規作成するユーザー名を決める。
    name クレームが取得できる場合はそれを優先し、
    取得できない場合はメールのローカル部にフォールバックする。
    """
    candidate = (google_name or "").strip()
    if not candidate:
        candidate = (email.split("@")[0] or "").strip()
    if not candidate:
        return "google_user"
    candidate = re.sub(r"\s+", " ", candidate)
    return candidate[:150]

#Googleログイン
@require_POST
@csrf_protect
def google_login_api(request):
    # サーバー側に Google Client ID が設定されているか確認
    # 未設定だとトークンの正当性を検証できないため 500 を返す。
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        return JsonResponse({"ok": False, "error": "google_client_id_not_configured"}, status=500)

    # フロントから受け取った ID トークン(credential)を取り出す。
    # JSONで送られてこない/空なら不正リクエストとして 400。
    data = _json(request)
    credential = (data.get("credential") or "").strip()
    if not credential:
        return JsonResponse({"ok": False, "error": "credential_required"}, status=400)

    try:
        # Googleの公開鍵で署名検証 + audience(client_id)検証を行う。
        # verifyに失敗したトークンは信用できないため 401。
        info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_google_token"}, status=401)

    sub = info.get("sub")
    email = (info.get("email") or "").lower()
    google_name = (info.get("name") or "").strip()
    if not google_name:
        given_name = (info.get("given_name") or "").strip()
        family_name = (info.get("family_name") or "").strip()
        google_name = " ".join(v for v in (given_name, family_name) if v).strip()
    email_verified = bool(info.get("email_verified"))
    # ログインに必要なクレームを検証。
    # sub: Googleアカウントを一意に表すID
    # email: アプリ側の一意キーとして利用
    # email_verified: 未検証メールでのログインを防ぐ
    if not sub or not email or not email_verified:
        return JsonResponse({"ok": False, "error": "invalid_google_payload"}, status=403)

    with transaction.atomic():
        # google_uid で既存連携済みユーザーを優先取得する。
        # これが見つかれば、そのユーザーでログインする。
        user = User.objects.select_for_update().filter(google_uid=sub).first()
        is_new = False

        if not user:
            # google_uid が未連携なら email で既存ユーザーを探す。
            # email は unique=True なので該当は最大1件。
            user = User.objects.select_for_update().filter(email__iexact=email).first()
            if user:
                # 既存ユーザーが見つかった場合:
                # google_uid が空なら今回の sub を紐付ける
                # 別subが既に紐づいていれば競合として 409
                if user.google_uid and user.google_uid != sub:
                    return JsonResponse({"ok": False, "error": "google_uid_conflict"}, status=409)
                user.google_uid = sub
                user.save(update_fields=["google_uid"])
            else:
                # email 一致ユーザーがいなければ新規作成。
                # username は重複可 (unique=False)
                # email は重複禁止 (unique=True)
                user = User(
                    email=email,
                    username=_username_from_google_profile(email, google_name),
                    google_uid=sub,
                )
                user.set_unusable_password()
                user.save()
                create_default_categories(user)
                is_new = True

    # Djangoセッションを発行してログイン完了。
    login(request, user)

    # 新規登録ユーザーのみテーマ選択を挟み、既存はダッシュボードへ。
    if is_new:
        request.session["show_theme_choice"] = True
        return JsonResponse({"ok": True, "redirect_to": reverse("signup_theme_choice")})

    return JsonResponse({"ok": True, "redirect_to": reverse("dashboard")})

# サインアップ
@ensure_csrf_cookie
def signup_page(request):
    # POSTリクエスト
    if request.method == "POST":
        form = EmailUserCreationForm(request.POST)
        profile_image = request.FILES.get("profile_image")

        # バリデーションOKならユーザー作成
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    create_default_categories(user)

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
                request.session["show_theme_choice"] = True
                return redirect("signup_theme_choice")

    # GETリクエスト
    else:
        form = EmailUserCreationForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required(login_url="login")
@ensure_csrf_cookie
def signup_theme_choice_page(request):
    if not request.session.get("show_theme_choice"):
        return redirect("dashboard")
    return render(request, "accounts/theme-choice.html")


@login_required(login_url="login")
@require_POST
@csrf_protect
def signup_theme_choice_complete_api(request):
    request.session.pop("show_theme_choice", None)
    return JsonResponse({"ok": True})


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
        "google_client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
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
    weeks = [dates[i : i + 7] for i in range(0, len(dates), 7)]

    # 前月・次月の年月を計算（ナビゲーション用）
    prev_y, prev_m = add_month(year, month, -1)
    next_y, next_m = add_month(year, month, 1)

    month_name = calendar.month_name[month]  # February

    # カレンダーに表示している最初と最後の日付
    # （前月・次月の分も含める）
    start_date = weeks[0][0]
    # 週の数が何個あるか分からないけど、一番最後の週[last_week_day0, last_week_day1, ..., last_week_day6]  # weeks[-1]
    end_date = weeks[-1][-1]

    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])

    # ★合算対応：選択中グループのメンバー全員（未選択なら自分だけ）
    scope_user_ids = get_scope_user_ids(request)

    # 表示範囲の日付だけを対象にする
    qs = (
        MoneyFlow.objects.select_related("category", "category__user")
        .filter(category__user_id__in=scope_user_ids, expense_date__range=(start_date, end_date))
    )

    month_qs = (
        MoneyFlow.objects.select_related("category")
        .filter(category__user_id__in=scope_user_ids, expense_date__range=(month_start, month_end))
    )

    month_in_total = 0
    month_out_total = 0
    for e in month_qs:
        if e.category.is_income:
            month_in_total += int(e.amount)
        else:
            month_out_total += int(e.amount)
    month_balance = month_in_total - month_out_total

    # 日付ごとの「収入」「支出」をまとめる入れ物
    # 例: daily["2026-01-29"] = {"in": 5000, "out": 1200}
    daily = defaultdict(lambda: {"in": 0, "out": 0})

    for e in qs:
        # 日付を "YYYY-MM-DD" 形式の文字列にする
        key = e.expense_date.isoformat()

        # category.is_io_type が 1 なら収入、そうでなければ支出
        if e.category.is_income:
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

            row.append(
                {
                    "date": d,  # date型
                    "ds": ds,  # "YYYY-MM-DD"
                    "day": d.day,  # 日だけ（数字）
                    "in_month": (d.month == month),  # 今月かどうか
                    "is_today": (d == today),  # 今日かどうか
                    "in_total": t["in"],  # その日の収入合計
                    "out_total": t["out"],  # その日の支出合計
                }
            )
        weeks_view.append(row)

    # テンプレートにデータを渡して描画
    return render(
        request,
        "dashboard/calendar.html",
        {
            "weeks": weeks_view,  # カレンダー本体
            "month": month,
            "year_label": year,
            "month_num": month,
            "month_name": month_name,
            "prev_ym": f"{prev_y:04d}-{prev_m:02d}",  # 前月リンク用（年4桁・月2桁ゼロ埋め）
            "next_ym": f"{next_y:04d}-{next_m:02d}",  # 次月リンク用（年4桁・月2桁ゼロ埋め）
            "today": today,
            "month_in_total": month_in_total,
            "month_out_total": month_out_total,
            "month_balance": month_balance,
        },
    )


# 支出リスト（共有対象）
@login_required(login_url="login")
@ensure_csrf_cookie
def dashboard_list_page(request):
    scope_user_ids = get_scope_user_ids(request)

    qs = (
        MoneyFlow.objects.select_related("category__user", "category")
        .filter(category__user_id__in=scope_user_ids)
        .order_by("-expense_date", "-id")
    )

    grouped_expenses = defaultdict(list)
    for e in qs:
        u = e.category.user
        can_edit = bool(u and u.id == request.user.id)
        grouped_expenses[e.expense_date].append(
            {
                "id": e.id,
                "amount": e.amount,
                "amount_sign": "+" if e.category.is_income else "-",
                "mode": "income" if e.category.is_income else "expense",
                "category": e.category.name,
                "categoryColor": e.category.color,
                "icon_key": e.category.icon_key,
                "title": e.title,
                "can_edit": can_edit,
                "owner_username": (u.username if u else ""),
                "owner_email": (u.email if u else ""),
                "owner_image_url": (u.image_url if u else None),
            }
        )

    sorted_grouped_expenses = sorted(grouped_expenses.items(), key=lambda item: item[0], reverse=True)

    return render(
        request,
        "dashboard/list/list.html",
        {"grouped_expenses": sorted_grouped_expenses},
    )


# 収支入力
@login_required(login_url="login")
def dashboard_moneyflow_form_page(request):
    mode = (request.POST.get("mode") or request.GET.get("mode") or "expense").strip()
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
            "is_income": bool(cat.is_income),
            "is_builtin": bool(cat.is_builtin),
        }

    expense_qs = Category.objects.filter(query, is_income=False).order_by("id")
    income_qs = Category.objects.filter(query, is_income=True).order_by("id")
    expense_categories = [normalize_category(cat) for cat in expense_qs]
    income_categories = [normalize_category(cat) for cat in income_qs]

    categories = income_categories if mode == "income" else expense_categories

    if request.method == "POST":
        # if mode == "receipt":
        #     return JsonResponse({"ok": False, "error": "receiptはまだ未実装だよ"}, status=400)

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

        if mode in ("expense", "receipt") and cat.is_income:
            return JsonResponse({"ok": False, "error": "支出タブでは収入カテゴリは選べないよ"}, status=400)
        if mode == "income" and (not cat.is_income):
            return JsonResponse({"ok": False, "error": "収入タブでは支出カテゴリは選べないよ"}, status=400)

        created = MoneyFlow.objects.create(
            category=cat,
            amount=amount,
            expense_date=expense_date,
            title=title,
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
            "expense_categories": expense_categories,
            "income_categories": income_categories,
            "mode_expense": (mode == "expense"),
            "mode_income": (mode == "income"),
            "mode_receipt": (mode == "receipt"),
            "user_name": user_name,
        },
    )

@login_required(login_url="login")
@require_POST
@csrf_protect
def receipt_analyze_api(request):
    receipt_image = request.FILES.get("receipt_image")
    if not receipt_image:
        return JsonResponse({"ok": False, "error": "receipt_image_required"}, status=400)

    query = _category_query_for_user(request.user)
    expense_categories = list(
        Category.objects.filter(query, is_income=False)
        .order_by("id")
        .values("id", "name")
    )
    allowed_category_ids = {c["id"] for c in expense_categories}

    try:
        image_bytes, meta = compress_and_resize_receipt(
            receipt_image,
            max_side=1600,
            max_bytes=settings.BEDROCK_RECEIPT_MAX_BYTES,
        )
        result = analyze_receipt_with_bedrock(
            image_bytes,
            media_type=meta["content_type"],
            categories=expense_categories,
        )
        if not isinstance(result, dict):
            raise ValueError("invalid_model_response")

        suggested_raw = result.get("suggested_category_id", result.get("category_id"))
        suggested_id = None
        if suggested_raw is not None and str(suggested_raw).strip() != "":
            try:
                suggested_id = int(str(suggested_raw).strip())
            except (TypeError, ValueError):
                suggested_id = None

        if suggested_id not in allowed_category_ids:
            suggested_id = None

        result["suggested_category_id"] = suggested_id

        title_raw = (
            result.get("title")
            or result.get("store_name")
            or result.get("merchant_name")
            or result.get("shop_name")
        )
        title_text = ""
        if isinstance(title_raw, str):
            title_text = re.sub(r"\s+", " ", title_raw).strip()
        if title_text:
            title_text = title_text[:255]
            result["title"] = title_text
        else:
            result["title"] = None

    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    
    except Exception as e:
        logger.exception("receipt analyze failed")
        payload = {"ok": False, "error": "receipt_analyze_failed"}
        if settings.DEBUG:
            payload["detail"] = str(e)
        return JsonResponse(payload, status=500)

    return JsonResponse({"ok": True, "result": result})

# カテゴリ管理
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
    base_qs = Category.objects.filter(query).order_by("id")

    expense_categories_raw = base_qs.filter(is_income=False)
    income_categories_raw = base_qs.filter(is_income=True)

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
    # 合算カテゴリは今はやらない（自分だけ）
    return Q(user=user)


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

    is_income = bool(is_io_type)
    query = _category_query_for_user(request.user)

    limit = MAX_EXPENSE_CATEGORIES if is_io_type == 0 else MAX_INCOME_CATEGORIES
    current_count = Category.objects.filter(query, is_income=is_income).count()
    if current_count >= limit:
        return JsonResponse({"ok": False, "error": "これ以上カテゴリは追加できないよ"}, status=409)

    exists = Category.objects.filter(query, is_income=is_income, name=name).exists()
    if exists:
        return JsonResponse({"ok": False, "error": "同じ名前のカテゴリが既にあるよ"}, status=409)

    cat = Category.objects.create(
        user=request.user,
        group=None,
        name=name,
        color=color,
        is_income=is_income,
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
                "is_income": cat.is_income,
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

    if cat.name in IMMUTABLE_CATEGORY_NAMES:
        return JsonResponse({"ok": False, "error": "このカテゴリは変更できないよ"}, status=400)

    exists = (
        Category.objects.filter(query, is_income=cat.is_income, name=name)
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
        mode = "income" if entry.category.is_income else "expense"

    query = _category_query_for_user(request.user)

    def normalize_category(cat: Category):
        icon_key = cat.icon_key if cat.icon_key in CATEGORY_ICON_KEYS else "default"
        color = cat.color if CATEGORY_COLOR_RE.match(cat.color or "") else "#999999"
        return {
            "id": cat.id,
            "name": cat.name,
            "icon_key": icon_key,
            "color": color,
            "is_income": bool(cat.is_income),
            "is_builtin": bool(cat.is_builtin),
        }

    expense_qs = Category.objects.filter(query, is_income=False).order_by("id")
    income_qs = Category.objects.filter(query, is_income=True).order_by("id")
    expense_categories = [normalize_category(cat) for cat in expense_qs]
    income_categories = [normalize_category(cat) for cat in income_qs]
    categories = income_categories if mode == "income" else expense_categories

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

        if mode in ("expense", "receipt") and cat.is_income:
            return JsonResponse({"ok": False, "error": "支出タブでは収入カテゴリは選べないよ"}, status=400)
        if mode == "income" and (not cat.is_income):
            return JsonResponse({"ok": False, "error": "収入タブでは支出カテゴリは選べないよ"}, status=400)

        entry.category = cat
        entry.amount = amount
        entry.expense_date = expense_date
        entry.title = title
        entry.save(update_fields=["category", "amount", "expense_date", "title"])

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
            "expense_categories": expense_categories,
            "income_categories": income_categories,
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


def create_nested_defaultdict_int():
    return defaultdict(int)


def build_charts_payload(request):
    get_user_ids = get_scope_user_ids(request)
    qs = (
        MoneyFlow.objects.select_related("category", "category__user")
        .filter(category__user_id__in=get_user_ids)
        .order_by("-expense_date", "-id")
    )
    all_expenses = list(qs)  # 全期間の生データを取得

    # 年ごとの集計用
    yearly_totals = defaultdict(create_nested_defaultdict_int)
    yearly_colors = {}

    # 月ごとの集計用
    monthly_totals = defaultdict(create_nested_defaultdict_int)
    monthly_colors = {}

    # 年の処理
    current_year_str = request.GET.get("year")
    if current_year_str:
        current_year = int(current_year_str)
    else:
        current_year = date.today().year
    prev_year = current_year - 1
    next_year = current_year + 1

    # 月の処理
    current_month_str = request.GET.get("month")
    if current_month_str:
        try:
            year_part, month_part = map(int, current_month_str.split("-"))
            current_month_date = date(year_part, month_part, 1)
        except ValueError:
            current_month_date = date(current_year, date.today().month, 1)
    else:
        current_month_date = date(current_year, date.today().month, 1)
    current_month_key = f"{current_month_date.year}-{current_month_date.month:02d}"

    # python-dateutil を使わない場合の prev_month_date と next_month_date の計算
    # 前の月を計算
    if current_month_date.month == 1:  # 1月の場合
        prev_month_date = date(current_month_date.year - 1, 12, 1)  # 前年の12月
    else:
        prev_month_date = date(
            current_month_date.year, current_month_date.month - 1, 1
        )  # 前の月
    # 次の月を計算
    if current_month_date.month == 12:  # 12月の場合
        next_month_date = date(current_month_date.year + 1, 1, 1)  # 次の年の1月
    else:
        next_month_date = date(
            current_month_date.year, current_month_date.month + 1, 1
        )  # 次の月
    prev_month_key = f"{prev_month_date.year}-{prev_month_date.month:02d}"
    next_month_key = f"{next_month_date.year}-{next_month_date.month:02d}"

    # 現在の表示期間タイプを決定 (JavaScriptに渡すため)
    current_period_type = "month" if current_month_str else "year"

    for e in all_expenses:
        expense_year = e.expense_date.year
        expense_month = e.expense_date.month
        category_name = e.category.name or "Unknwn"
        amount = int(e.amount)
        # 年ごとの集計
        yearly_totals[expense_year][category_name] += amount
        if category_name not in yearly_colors and e.category.color:
            yearly_colors[category_name] = e.category.color
        year_month_key = f"{expense_year}-{expense_month:02d}"
        # 月ごとの集計 (例: "2026-02")
        monthly_totals[year_month_key][category_name] += amount
        if category_name not in monthly_colors and e.category.color:
            monthly_colors[category_name] = e.category.color

    # 現在の年データ
    current_yearly_data = yearly_totals[current_year]
    yearly_labels = list(current_yearly_data.keys())

    yearly_values = []  # まず空のリストを初期化する
    for label in yearly_labels:  # yearly_labels の各要素をループする
        value = current_yearly_data[label]  # 各ラベルに対応する値を取得する
        yearly_values.append(value)  # 各ラベルに対応する値を取得する

    yearly_bg = []  # まず空のリストを初期化する
    for label in yearly_labels:  # yearly_labels の各要素をループする
        color = yearly_colors.get(
            label, "#999999"
        )  # 各ラベルに対応する色を取得する。見つからなければ "#999999" を使う
        yearly_bg.append(color)  # 取得した色をリストに追加する

    yearly_total_amount = sum(yearly_values)
    yearly_formatted_total_amount = f"¥{yearly_total_amount:,}"

    # 現在の月データ
    current_monthly_data = monthly_totals[current_month_key]
    monthly_labels = list(current_monthly_data.keys())

    monthly_values = []  # まず空のリストを初期化する
    for label in monthly_labels:  # monthly_labels の各要素をループする
        value = current_monthly_data[label]  # 各ラベルに対応する値を取得する
        monthly_values.append(value)  # 取得した値をリストに追加する

    monthly_bg = []  # まず空のリストを初期化する
    for label in monthly_labels:  # monthly_labels の各要素をループする
        color = monthly_colors.get(
            label, "#999999"
        )  # 各ラベルに対応する色を取得する。見つからなければ "#999999" を使う
        monthly_bg.append(color)  # 取得した色をリストに追加する

    monthly_total_amount = sum(monthly_values)
    monthly_formatted_total_amount = f"¥{monthly_total_amount:,}"

    processed_chart_data = {
        "year": {
            "labels": yearly_labels,
            "values": yearly_values,
            "bg": yearly_bg,
            "formattedTotalAmount": yearly_formatted_total_amount,
            "currentYearDisplay": current_year,
        },
        "month": {
            "labels": monthly_labels,
            "values": monthly_values,
            "bg": monthly_bg,
            "formattedTotalAmount": monthly_formatted_total_amount,
            "currentYearDisplay": current_year,
            "currentMonthKey": current_month_key,
        },
    }

    return {
        "processed_chart_data": processed_chart_data,
        "current_year_display": current_year,
        "prev_year": prev_year,
        "next_year": next_year,
        "prev_month_key": prev_month_key,
        "next_month_key": next_month_key,
        "current_period_type": current_period_type,
        "year_label": current_month_date.year,
        "month_num": current_month_date.month,
    }

@login_required(login_url="login")
@ensure_csrf_cookie
def charts_page(request):
    context = build_charts_payload(request)
    return render(
        request,
        "dashboard/charts/chart.html",
        context,
    )


@login_required(login_url="login")
@require_GET
def charts_data_api(request):
    payload = build_charts_payload(request)
    payload["ok"] = True
    return JsonResponse(payload)


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

# ユーザーのプロフィール画像の更新API
@login_required(login_url="login")
@require_POST
def profile_image_update_api(request):
    # form-data の "profile_image" を受け取る（未選択なら400）
    profile_image = request.FILES.get("profile_image")
    if not profile_image:
        return JsonResponse({"ok": False, "error": "画像が未選択です"}, status=400)

    # content-type を最低限チェック（画像以外は受け付けない）
    content_type = profile_image.content_type or ""
    if not content_type.startswith("image/"):
        return JsonResponse({"ok": False, "error": "画像ファイルのみアップロード可能です"}, status=400)

    try:
        # 既存サービスを再利用して
        # 1) 3MB超なら圧縮 2) S3アップロード 3) 保存キー返却
        key = save_profile_image(request.user.id, profile_image)

        # 返却キーから公開URLを組み立てる
        base_url = settings.AWS_S3_BASE_URL or (
            f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"
        )
        image_url = f"{base_url.rstrip('/')}/{key.lstrip('/')}"

        # users.image_url を最新URLに更新
        request.user.image_url = image_url
        request.user.save(update_fields=["image_url"])
    except (BotoCoreError, ClientError, OSError, UnidentifiedImageError):
        # S3接続失敗 / 画像変換失敗などは500で返す
        return JsonResponse(
            {"ok": False, "error": "プロフィール画像の保存に失敗しました"},
            status=500,
        )

    # 成功時はフロントが即時反映できるようURLを返す
    return JsonResponse({"ok": True, "image_url": image_url})

# ユーザーネームの変更API
@login_required(login_url="login")
@require_POST
def account_username_update_api(request):
    # 期待フォーマット: {"username": "new_name"}
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "リクエスト形式が不正です"}, status=400)

    # username を取り出し、前後の空白を除去して正規化する
    username = (payload.get("username") or "").strip()

    # 入力チェック（空文字・長すぎる値を拒否）
    if not username:
        return JsonResponse({"ok": False, "error": "ユーザーネームを入力してください"}, status=400)
    if len(username) > 150:
        return JsonResponse({"ok": False, "error": "ユーザーネームは150文字以内で入力してください"}, status=400)

    # 同値更新はDB更新せず成功を返す
    if request.user.username == username:
        return JsonResponse({"ok": True, "username": username, "updated": False})

    # username を保存する
    request.user.username = username
    request.user.save(update_fields=["username"])

    # 成功レスポンス（最新値を返す）
    return JsonResponse({"ok": True, "username": request.user.username, "updated": True})


# メールアドレスの変更API
@login_required(login_url="login")
@require_POST
def account_user_email_update_api(request):
    # 期待フォーマット: {"email": "new@example.com"}
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "リクエスト形式が不正です"}, status=400)

    #　email を取り出して正規化（空白除去 + 小文字化）
    email = (payload.get("email") or "").strip().lower()

    #　入力チェック
    if not email:
        return JsonResponse({"ok": False, "error": "メールアドレスを入力してください"}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "メールアドレスの形式が不正です"}, status=400)

    #　同値更新はDB更新せず成功を返す
    if request.user.email == email:
        return JsonResponse({"ok": True, "email": email, "updated": False})

    #　先に重複確認を行う
    if User.objects.exclude(pk=request.user.pk).filter(email=email).exists():
        return JsonResponse({"ok": False, "error": "このメールアドレスは使用されています"}, status=409)

    #　email を保存する
    request.user.email = email
    try:
        request.user.save(update_fields=["email"])
    except IntegrityError:
        # 競合が同時に起きた場合の最終防衛
        return JsonResponse({"ok": False, "error": "このメールアドレスは使用されています"}, status=409)

    # 成功レスポンス（最新値を返す）
    return JsonResponse({"ok": True, "email": request.user.email, "updated": True})


# パスワードの変更API
@login_required(login_url="login")
@require_POST
def account_user_password_update_api(request):
    # 期待フォーマット:
    # {
    #   "current_password": "現在のパスワード",
    #   "new_password": "新しいパスワード",
    #   "new_password_confirm": "新しいパスワード(確認)"
    # }
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "リクエスト形式が不正です"}, status=400)

    current_password = payload.get("current_password") or ""
    new_password = payload.get("new_password") or ""
    new_password_confirm = payload.get("new_password_confirm") or ""

    if not current_password or not new_password or not new_password_confirm:
        return JsonResponse({"ok": False, "error": "すべての項目を入力してください"}, status=400)

    if new_password != new_password_confirm:
        return JsonResponse({"ok": False, "error": "新しいパスワードが一致しません"}, status=400)

    if not request.user.check_password(current_password):
        return JsonResponse({"ok": False, "error": "現在のパスワードが正しくありません"}, status=400)

    if current_password == new_password:
        return JsonResponse({"ok": False, "error": "現在と異なるパスワードを設定してください"}, status=400)

    try:
        # Django標準のパスワードバリデータを適用
        validate_password(new_password, user=request.user)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": " ".join(e.messages)}, status=400)

    # ハッシュ化して保存
    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])

    # パスワード変更後もログイン状態を維持する
    update_session_auth_hash(request, request.user)

    return JsonResponse({"ok": True, "updated": True})



@require_GET
def users_api(request):
    users = list(User.objects.values("id", "username", "email"))
    return JsonResponse({"users": users})


# ==========================
# Groups APIs（合算グループ）
# ==========================

@login_required(login_url="login")
@require_GET
def groups_available_api(request):
    me = request.user
    current_group_id = get_current_group_id(request)

    memberships = (
        ShareGroupMember.objects.select_related("share_group")
        .filter(user=me)
        .order_by("share_group__name")
    )

    groups = []
    for m in memberships:
        g = m.share_group
        groups.append(
            {
                "id": g.id,
                "name": g.name,
                "role": m.role,
            }
        )

    return JsonResponse(
        {
            "ok": True,
            "current_group_id": current_group_id,
            "personal": {"id": 0, "name": request.user.username or "自分"},
            "groups": groups,
        }
    )


@login_required(login_url="login")
@require_POST
@csrf_protect
def groups_select_api(request):
    data = _json(request)
    gid = data.get("group_id", None)

    # personalへ戻す
    if gid in (None, "", 0, "0"):
        request.session.pop(GROUP_SESSION_KEY, None)
        return JsonResponse({"ok": True, "current_group_id": None})

    try:
        gid = int(gid)
    except Exception:
        return JsonResponse({"ok": False, "error": "bad_request"}, status=400)

    if not can_use_group(gid, request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    request.session[GROUP_SESSION_KEY] = gid
    return JsonResponse({"ok": True, "current_group_id": gid})


@login_required(login_url="login")
@require_POST
@csrf_protect
def groups_create_api(request):
    data = _json(request)
    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "name_required"}, status=400)

    with transaction.atomic():
        g = ShareGroup.objects.create(name=name, created_by_user=request.user)
        ShareGroupMember.objects.create(share_group=g, user=request.user, role="owner")

    return JsonResponse({"ok": True, "group": {"id": g.id, "name": g.name}})


@login_required(login_url="login")
@require_GET
def groups_members_list_api(request, group_id: int):
    if not can_use_group(group_id, request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    ms = (
        ShareGroupMember.objects.select_related("user")
        .filter(share_group_id=group_id)
        .order_by("user__email")
    )

    members = [
        {
            "id": m.user.id,
            "email": m.user.email,
            "username": m.user.username,
            "role": m.role,
            "image_url": m.user.image_url,
        }
        for m in ms
    ]
    return JsonResponse({"ok": True, "members": members})


@login_required(login_url="login")
@require_POST
@csrf_protect
def groups_members_add_api(request, group_id: int):
    if not can_use_group(group_id, request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    data = _json(request)
    email = (data.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"ok": False, "error": "email_required"}, status=400)

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return JsonResponse({"ok": False, "error": "user_not_found"}, status=404)

    obj, created = ShareGroupMember.objects.get_or_create(
        share_group_id=group_id,
        user_id=user.id,
        defaults={"role": "member"},
    )
    return JsonResponse({"ok": True, "created": created})


@login_required(login_url="login")
@require_POST
@csrf_protect
def groups_members_remove_api(request, group_id: int):
    if not can_use_group(group_id, request.user):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    data = _json(request)
    try:
        user_id = int(data.get("user_id"))
    except Exception:
        return JsonResponse({"ok": False, "error": "bad_request"}, status=400)

    target = ShareGroupMember.objects.filter(share_group_id=group_id, user_id=user_id).first()
    if not target:
        return JsonResponse({"ok": True, "deleted": False})

    if target.role == "owner":
        return JsonResponse({"ok": False, "error": "cannot_remove_owner"}, status=409)

    deleted, _ = ShareGroupMember.objects.filter(id=target.id).delete()
    return JsonResponse({"ok": True, "deleted": bool(deleted)})


@login_required(login_url="login")
@require_POST
@csrf_protect
def groups_delete_api(request, group_id: int):
    link = ShareGroupMember.objects.filter(share_group_id=group_id, user=request.user).first()
    if not link or link.role != "owner":
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    group = ShareGroup.objects.filter(id=group_id).first()
    if not group:
        return JsonResponse({"ok": True, "deleted": False})

    group.delete()

    if get_current_group_id(request) == group_id:
        request.session.pop(GROUP_SESSION_KEY, None)

    return JsonResponse({"ok": True, "deleted": True})


# サインアップ（旧）
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
