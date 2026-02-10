# backend/web/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ---- USERS ----
# ---- UserCreatiomFormを対応させる ----
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    group = models.ForeignKey("ShareGroup", null=True, blank=True, on_delete=models.DO_NOTHING)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    icon = models.ImageField(upload_to="user_icons/", blank=True, null=True)
    google_uid = models.CharField(max_length=255, blank=True, null=True, unique=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []   # ← ここが重要

    class Meta:
        db_table = "USERS"



# ---- SHARE GROUP ----
class ShareGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    owner_user = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        db_column="owner_user_id",
        related_name="owned_groups",
    )
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "SHARE_GROUPS"
        


class Category(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="categories",
    )
    group = models.ForeignKey(
        ShareGroup,
        on_delete=models.DO_NOTHING,
        db_column="group_id",
        related_name="categories",
    )
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=20)
    is_in_type = models.BooleanField(db_column="is_in_type")
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "CATEGORIES"
    


class Receipt(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="receipts",
    )
    group = models.ForeignKey(
        ShareGroup,
        on_delete=models.DO_NOTHING,
        db_column="group_id",
        related_name="receipts",
    )
    image = models.ImageField(upload_to="receipts/", blank=True, null=True)
    ocr_status = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "RECEIPTS"
    


class MoneyFlow(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="money_flows",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.DO_NOTHING,
        db_column="category_id",
        related_name="money_flows",
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.DO_NOTHING,
        db_column="receipt_id",
        related_name="money_flows",
        blank=True,
        null=True,
    )
    group = models.ForeignKey(
        ShareGroup,
        on_delete=models.DO_NOTHING,
        db_column="group_id",
        related_name="money_flows",
    )
    amount = models.IntegerField()
    expense_date = models.DateField()
    memo = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "MONEY_FLOWS"
        


# class ReceiptItem(models.Model):
#     receipt = models.ForeignKey(
#         Receipt,
#         on_delete=models.DO_NOTHING,
#         db_column="receipt_id",
#         related_name="items",
#     )
#     category = models.ForeignKey(
#         Category,
#         on_delete=models.DO_NOTHING,
#         db_column="category_id",
#         related_name="receipt_items",
#     )
#     item_name = models.CharField(max_length=255)
#     price = models.IntegerField()
#     detection_date = models.DateField(blank=True, null=True)

#     class Meta:
#         db_table = "RECEIPT_ITEMS"
#         
