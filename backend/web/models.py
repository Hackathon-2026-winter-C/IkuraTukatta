# backend/web/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


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

# ---- USER ----    
class User(AbstractBaseUser, PermissionsMixin):
    group = models.ForeignKey(
        "ShareGroup",
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name="users"
    )
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    google_uid = models.CharField(max_length=255, blank=True, null=True, unique=True)


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


# ---- SHARE GROUP ----
class ShareGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_groups",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "SHARE_GROUPS"
      

# ---- CATEGORY ----
class Category(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    group = models.ForeignKey(
        ShareGroup,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=20)
    is_in_type = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CATEGORIES"


# ---- RECEIPT ----
class Receipt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="receipts",
    )
    group = models.ForeignKey(
        ShareGroup,
        on_delete=models.CASCADE,
        related_name="receipts",
    )
    image_url = models.CharField(max_length=2048, blank=True, null=True)
    ocr_status = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "RECEIPTS"
        

# ---- MONEY FLOW ----
class MoneyFlow(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="money_flows",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="money_flows",
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.SET_NULL,
        related_name="money_flows",
        blank=True,
        null=True,
    )
    group = models.ForeignKey(
        ShareGroup,
        on_delete=models.CASCADE,
        related_name="money_flows",
    )
    amount = models.IntegerField()
    expense_date = models.DateField()
    memo = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "MONEY_FLOWS"


