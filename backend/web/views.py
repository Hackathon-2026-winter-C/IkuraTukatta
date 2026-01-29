# backend/web/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from .models import InOrExp, AppUser
from collections import defaultdict
from datetime import date
import calendar


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
    users = list(
        AppUser.objects.values("id","name","email")
    )
    return JsonResponse({"users": users})

@ensure_csrf_cookie
def test_footer_page(request):
    return render(request, "sample/test_footer.html")

@ensure_csrf_cookie
def login_page(request):
    return render(request, 'accounts/login.html')

@ensure_csrf_cookie
def signup_page(request):
    return render(request, 'accounts/signup.html')

@ensure_csrf_cookie
def dashboard_list_page(request):
    return render(request, 'dashboard/list/list.html')

@ensure_csrf_cookie
def dashboard_moneyflow_form_page(request):
    return render(request, 'dashboard/moneyflow/moneyflow_form.html')

@ensure_csrf_cookie
def dashboard_moneyflow_category_page(request):
    return render(request, 'dashboard/moneyflow/category.html')

@ensure_csrf_cookie
def dashboard_moneyflow_edit_page(request):
    return render(request, 'dashboard/moneyflow/moneyflow_edit.html')

@ensure_csrf_cookie
def account_page(request):
    return render(request, 'accounts/account.html')

