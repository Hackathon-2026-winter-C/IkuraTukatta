# backend/web/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from .models import InOrExp, AppUser

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
    user_email = "alice@example.com"
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
    today = date.today()
    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(today.year, today.month)
    month_label = f"{today.year}年{today.month}月"

    return render(
        request,
        "dashboard/calendar.html",
        {"weeks": weeks, "month_label": month_label, "today_day": today.day},
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

