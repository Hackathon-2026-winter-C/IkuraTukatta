from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    group = models.ForeignKey(
        "ShareGroup",
        on_delete=models.SET_NULL,
        db_column="group_id",
        null=True,
        blank=True,
        related_name="members",
    )
    image_url = models.CharField(max_length=2048, null=True, blank=True)
    google_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD="email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "USERS"


class ShareGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    owner_user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        db_column="owner_user_id",
        related_name="owned_groups",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "SHARE_GROUPS"
        constraints = [
            models.UniqueConstraint(
                fields=["owner_user", "name"],
                name="uq_sharegroup_owner_name",
            ),
        ]


class Category(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        db_column="user_id",
        null=True,
        blank=True,
        related_name="categories",
    )
    group = models.ForeignKey(
        "ShareGroup",
        on_delete=models.SET_NULL,
        db_column="group_id",
        null=True,
        blank=True,
        related_name="categories",
    )
    name = models.CharField(max_length=255)
    color = models.CharField(
        max_length=7,
        validators=[RegexValidator(regex=r"^#[0-9A-Fa-f]{6}$")],
    )
    is_in_type = models.BooleanField()
    icon_key = models.CharField(max_length=50)
    is_builtin = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CATEGORIES"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="uq_category_user_name",
            ),
            models.UniqueConstraint(
                fields=["group", "name"],
                name="uq_category_group_name",
            ),
        ]


class MoneyFlow(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        "Category",
        on_delete=models.PROTECT,
        db_column="category_id",
        related_name="money_flows",
    )

    amount = models.DecimalField(max_digits=10, decimal_places=0)
    expense_date = models.DateField()
    memo = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "MONEY_FLOWS"

