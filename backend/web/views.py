# backend/web/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .models import InOrExp, AppUser, Category
from collections import defaultdict
from datetime import date
import calendar
import json

# ===== Category 上限 =====
# 画面側の「＋（追加ボタン）」の最大数も、この上限に合わせる
MAX_EXPENSE_CATEGORIES = 16
MAX_INCOME_CATEGORIES = 8

@ensure_csrf_cookie
def index_page(request):
    expenses = (
        InOrExp.objects.select_related("user", "category")
        .order_by("-expense_date", "-id")
    )
    return render(request, "index.html", {"expenses": expenses})


@ensure_csrf_cookie
def settings_page(request):
    return render(request, "settings.html")


@ensure_csrf_cookie
def user_page(request):
    return render(request, "user.html")


@ensure_csrf_cookie
def signup_view(request):
    return render(request, "accounts/signup.html")


@ensure_csrf_cookie
def charts_page(request):
    user_email = "haruto@example.com"
    qs = (
        InOrExp.objects.select_related("user", "category")
        .filter(user__email=user_email)
        .order_by("-expense_date", "-id")
    )
    expense_list = list(qs)
    first = expense_list[0] if expense_list else None
    user_name = first.user.name if first and first.user and first.user.name else user_email

    expense_data = [
        {
            "date": e.expense_date.isoformat(),
            "amount": e.amount,
            "category": e.category.name,
            "categoryColor": e.category.color,
            "memo": e.memo,
            "user": e.user.name,
        }
        for e in expense_list
    ]
    return render(
        request,
        "dashboard/charts/chart.html",
        {"expense_data": expense_data, "user_name": user_name},
    )


@ensure_csrf_cookie
def dashboard_page(request):
    # 今日の日付を取得（「今日」のマスを強調表示するために使う）
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

    # 仮のユーザー（ログイン機能ができるまで）
    user_email = "haruto@example.com"

    # DBからこのユーザーのデータを取得
    # 表示範囲の日付だけを対象にする
    qs = (
        InOrExp.objects.select_related("category", "user")
        .filter(user__email=user_email, expense_date__range=(start_date, end_date))
    )

    # デバッグ用：ちゃんとデータが取れているか確認
    print("user_email:", user_email)
    print("qs_count:", qs.count())
    print("first_5:", list(qs.values("expense_date", "amount")[:5]))

    # 日付ごとの「収入」「支出」をまとめる入れ物
    # 例: daily["2026-01-29"] = {"in": 5000, "out": 1200}
    daily = defaultdict(lambda: {"in": 0, "out": 0})

    for e in qs:
        # 日付を "YYYY-MM-DD" 形式の文字列にする
        key = e.expense_date.isoformat()

        # category.is_io_type が 1 なら収入、そうでなければ支出
        if getattr(e.category, "is_io_type", 0) == 1:
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


@require_GET
def users_api(request):
    users = list(AppUser.objects.values("id", "name", "email"))
    return JsonResponse({"users": users})


@ensure_csrf_cookie
def test_footer_page(request):
    return render(request, "sample/test_footer.html")


@ensure_csrf_cookie
def login_page(request):
    return render(request, "accounts/login.html")


@ensure_csrf_cookie
def signup_page(request):
    return render(request, "accounts/signup.html")


@ensure_csrf_cookie
def dashboard_list_page(request):
    return render(request, "dashboard/list/list.html")


@ensure_csrf_cookie
def dashboard_moneyflow_form_page(request):
    return render(request, "dashboard/moneyflow/moneyflow_form.html")


@ensure_csrf_cookie
def dashboard_moneyflow_edit_page(request):
    return render(request, "dashboard/moneyflow/moneyflow_edit.html")


@ensure_csrf_cookie
def account_page(request):
    return render(request, "accounts/account.html")

@ensure_csrf_cookie
def dashboard_moneyflow_category_page(request):
    # -----------------------------
    # カテゴリ一覧ページ表示用のView
    # -----------------------------
    # ensure_csrf_cookie:
    #   HTMLを返すときにCSRFトークンのcookieをセットしてくれる
    #   → このページでJSのfetch(POST)を使う場合にCSRFが必要になるので先に用意しておく

    # 仮固定（haruto / group 1）
    # 本来はログインユーザーから user_id / group_id を取る（request.user など）
    user_id = 1
    group_id = 1

    # 支出カテゴリ一覧（is_io_type=0 を支出として扱う）
    expense_categories = Category.objects.filter(
        user_id=user_id,
        group_id=group_id,
        is_io_type=0,
    ).order_by("id")

    # 収入カテゴリ一覧（is_io_type=1 を収入として扱う）
    income_categories = Category.objects.filter(
        user_id=user_id,
        group_id=group_id,
        is_io_type=1,
    ).order_by("id")

    # ★ 最大数ベースで「残り枠＝＋の数（プレースホルダー）」を決める
    # 例：支出が今10個なら、16-10=6 → 6個分「＋」枠を表示できる
    expense_count = expense_categories.count()
    income_count = income_categories.count()

    # range(n) をテンプレに渡して、forループで「＋」枠をn個描画する想定
    # max(0, ...) にしておくことで、万一上限を超えていてもマイナスにならない
    expense_placeholders = range(max(0, MAX_EXPENSE_CATEGORIES - expense_count))
    income_placeholders = range(max(0, MAX_INCOME_CATEGORIES - income_count))

    # テンプレに必要なものを渡して描画
    return render(
        request,
        "dashboard/moneyflow/category.html",
        {
            "expense_categories": expense_categories,
            "income_categories": income_categories,
            "expense_placeholders": expense_placeholders,
            "income_placeholders": income_placeholders,
            # 上限値もテンプレ側に渡す（表示文言やバリデーション表示に使える）
            "max_expense": MAX_EXPENSE_CATEGORIES,
            "max_income": MAX_INCOME_CATEGORIES,
        },
    )


def _json(request):
    # -----------------------------
    # request.body（bytes）からJSONを安全に取り出すヘルパー
    # -----------------------------
    # JS fetchで送ったJSONを読む想定:
    #   fetch(url, {method:"POST", body: JSON.stringify({...})})
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        # JSONじゃなかった / 空だった / 文字コード変だった等でも落ちないように
        return {}


@require_POST
@csrf_protect
def category_create_api(request):
    # -----------------------------
    # カテゴリ新規作成API（POST）
    # -----------------------------
    # require_POST:
    #   GETで叩かれたら405にしてくれる（APIとして安全）
    # csrf_protect:
    #   CSRFトークンが無いPOSTを拒否（Djangoの標準セキュリティ）

    # 仮固定（haruto / group 1）
    user_id = 1
    group_id = 1

    # JSONを読み取り
    data = _json(request)

    # name: 前後の空白を削って、空文字なら弾く
    name = (data.get("name") or "").strip()

    # color: 送られなかったらデフォルトを入れる
    # ※今「#C5C5C5固定にする」なら、ここを "#C5C5C5" にすると統一できる
    color = (data.get("color") or "#FF9400").strip()

    # is_io_type: 0=支出 / 1=収入（フロントから数値で来る想定）
    is_io_type = data.get("is_io_type")

    # 収支区分チェック：0か1以外は不正
    if is_io_type not in (0, 1):
        return JsonResponse({"ok": False, "error": "is_io_type must be 0 or 1"}, status=400)

    # 名前必須
    if not name:
        return JsonResponse({"ok": False, "error": "name is required"}, status=400)

    # ★ DBの件数で上限制限（支出16 / 収入8）
    # 画面表示上「＋」枠が残ってても、DB側で最終防衛する（重要）
    current_count = Category.objects.filter(
        user_id=user_id,
        group_id=group_id,
        is_io_type=is_io_type,
    ).count()

    # 区分ごとに上限を変える
    limit = MAX_EXPENSE_CATEGORIES if is_io_type == 0 else MAX_INCOME_CATEGORIES
    if current_count >= limit:
        # 409: Conflict（追加したいけど制約で無理、のときに相性が良い）
        return JsonResponse({"ok": False, "error": "これ以上カテゴリは追加できないよ"}, status=409)

    # 同名チェック（同じ user/group/収支区分で重複禁止）
    # 例：支出に「食費」があるのに、また「食費」を作らせない
    exists = Category.objects.filter(
        user_id=user_id,
        group_id=group_id,
        is_io_type=is_io_type,
        name=name,
    ).exists()
    if exists:
        return JsonResponse({"ok": False, "error": "同じ名前のカテゴリが既にあるよ"}, status=409)

    # DBに新規作成
    cat = Category.objects.create(
        user_id=user_id,
        group_id=group_id,
        is_io_type=is_io_type,
        name=name,
        color=color,
        is_builtin=False,  # ユーザー追加カテゴリ（デフォルトカテゴリ等と区別するため）
    )

    # フロントに必要な情報だけ返す（テンプレ差し替えやDOM追加に使う）
    return JsonResponse(
        {
            "ok": True,
            "category": {
                "id": cat.id,
                "name": cat.name,
                "color": cat.color,
                "is_io_type": cat.is_io_type,
            },
        }
    )


@require_POST
@csrf_protect
def category_rename_api(request, category_id: int):
    # -----------------------------
    # カテゴリ名変更API（POST）
    # -----------------------------
    # URLで category_id を受け取る（例: /api/category/123/rename みたいな）
    # そのIDが「今のユーザーのカテゴリか？」までチェックするのが重要

    user_id = 1
    group_id = 1

    data = _json(request)
    name = (data.get("name") or "").strip()

    # 名前必須
    if not name:
        return JsonResponse({"ok": False, "error": "name is required"}, status=400)

    # 対象カテゴリ取得（user_id / group_id も条件に入れて他人のカテゴリを触れないようにする）
    try:
        cat = Category.objects.get(id=category_id, user_id=user_id, group_id=group_id)
    except Category.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    # 「その他」は変更不可（仕様として固定したいカテゴリ）
    # ※デフォルトカテゴリに該当するなら is_builtin でも縛れる
    if cat.name in ("支出その他", "収入その他", "その他"):
        return JsonResponse({"ok": False, "error": "「その他」は変更できないよ"}, status=400)

    # リネーム先の同名チェック（自分自身は除外する）
    # 例：id=5を「食費」に変えようとしたら、既に「食費」がある場合はNG
    exists = Category.objects.filter(
        user_id=user_id,
        group_id=group_id,
        is_io_type=cat.is_io_type,  # 同じ収支区分内で重複禁止
        name=name,
    ).exclude(id=cat.id).exists()

    if exists:
        return JsonResponse({"ok": False, "error": "同じ名前のカテゴリが既にあるよ"}, status=409)

    # 更新
    cat.name = name
    # update_fields を指定すると「そのカラムだけ更新」で意図が明確になる
    cat.save(update_fields=["name"])

    return JsonResponse({"ok": True, "category": {"id": cat.id, "name": cat.name}})

@require_POST
@csrf_protect
def category_delete_api(request, category_id: int):
    user_id = 1
    group_id = 1

    # 対象カテゴリ取得（他人のカテゴリ触れない）
    try:
        cat = Category.objects.get(id=category_id, user_id=user_id, group_id=group_id)
    except Category.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    # デフォルトカテゴリは削除不可
    if getattr(cat, "is_builtin", False):
        return JsonResponse({"ok": False, "error": "このカテゴリは削除できないよ"}, status=400)

    # 念のため「その他」系もガード
    if cat.name in ("支出その他", "収入その他", "その他"):
        return JsonResponse({"ok": False, "error": "「その他」は削除できないよ"}, status=400)

    # 使われてるカテゴリは削除禁止（安全）
    used = InOrExp.objects.filter(category_id=cat.id).exists()
    if used:
        return JsonResponse({"ok": False, "error": "このカテゴリは既に記録に使われてるから削除できないよ"}, status=409)

    cat.delete()
    return JsonResponse({"ok": True, "deleted_id": category_id})
