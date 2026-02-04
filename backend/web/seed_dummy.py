from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from web.models import Category, MoneyFlow, User


@transaction.atomic
def seed():
    user, created = User.objects.get_or_create(
        email="demo@example.com",
        defaults={"username": "demo"},
    )
    if created or not user.has_usable_password():
        user.set_password("demo1234")
        user.save(update_fields=["password"])

    category_specs = [
        ("食費", False, "food", 12),
        ("住居費", False, "home", 20),
        ("交通費", False, "transport", 30),
        ("光熱費", False, "utility", 40),
        ("日用品", False, "daily", 50),
        ("娯楽", False, "entertainment", 60),
        ("洋服", False, "clothes", 70),
        ("医療費", False, "medical", 80),
        ("給料", True, "salary", 90),
    ]

    categories = {}
    for name, is_in_type, icon_key, color in category_specs:
        cat, _ = Category.objects.update_or_create(
            user=user,
            group=None,
            name=name,
            defaults={
                "color": color,
                "is_in_type": is_in_type,
                "icon_key": icon_key,
                "is_builtin": False,
            },
        )
        categories[name] = cat

    today = timezone.localdate()
    start = today - timedelta(days=59)

    MoneyFlow.objects.filter(
        category__in=[categories[name] for name, *_ in category_specs],
        memo__startswith="seed:",
        expense_date__range=(start, today),
    ).delete()

    expense_names = ["食費", "住居費", "交通費", "光熱費", "日用品", "娯楽", "洋服", "医療費"]
    base_amounts = {
        "食費": 900,
        "住居費": 3000,
        "交通費": 600,
        "光熱費": 1200,
        "日用品": 700,
        "娯楽": 1500,
        "洋服": 2000,
        "医療費": 1000,
    }

    weeks = ((today - start).days // 7) + 1
    for i in range(weeks):
        d = start + timedelta(days=i * 7)
        name = expense_names[i % len(expense_names)]
        amount = Decimal(base_amounts[name] + (i * 123) % 800)
        MoneyFlow.objects.create(
            category=categories[name],
            amount=amount,
            expense_date=d,
            memo=f"seed:{name}:{d.isoformat()}",
            receipt_id=None,
        )

    # 給料は各月の1日に入れる
    cursor = start.replace(day=1)
    while cursor <= today:
        if cursor >= start:
            MoneyFlow.objects.create(
                category=categories["給料"],
                amount=Decimal("250000"),
                expense_date=cursor,
                memo=f"seed:給料:{cursor.strftime('%Y-%m')}",
                receipt_id=None,
            )
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
