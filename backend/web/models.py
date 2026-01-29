# backend/web/models.py
from django.db import models


class AppUser(models.Model):
    group = models.ForeignKey(
        "ShareGroup",
        on_delete=models.DO_NOTHING,
        db_column="group_id",
        related_name="users",
        blank=True,
        null=True,
    )
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True, null=True)
    google_uid = models.CharField(max_length=255, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "USERS"
        managed = False


class ShareGroup(models.Model):
    name = models.CharField(max_length=255)
    owner_user = models.ForeignKey(
        AppUser,
        on_delete=models.DO_NOTHING,
        db_column="owner_user_id",
        related_name="owned_groups",
    )
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "SHARE_GROUPS"
        managed = False


class Category(models.Model):
    user = models.ForeignKey(
        AppUser,
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
    is_io_type = models.BooleanField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "CATEGORIES"
        managed = False


class Receipt(models.Model):
    user = models.ForeignKey(
        AppUser,
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
    image_url = models.CharField(max_length=2048, blank=True, null=True)
    taken_at = models.DateTimeField(blank=True, null=True)
    ocr_status = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "RECEIPTS"
        managed = False


class InOrExp(models.Model):
    user = models.ForeignKey(
        AppUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="in_or_exps",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.DO_NOTHING,
        db_column="category_id",
        related_name="in_or_exps",
    )
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.DO_NOTHING,
        db_column="receipt_id",
        related_name="in_or_exps",
        blank=True,
        null=True,
    )
    group = models.ForeignKey(
        ShareGroup,
        on_delete=models.DO_NOTHING,
        db_column="group_id",
        related_name="in_or_exps",
    )
    amount = models.IntegerField()
    expense_date = models.DateField()
    memo = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "IN_OR_EXPS"
        managed = False


class ReceiptItem(models.Model):
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.DO_NOTHING,
        db_column="receipt_id",
        related_name="items",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.DO_NOTHING,
        db_column="category_id",
        related_name="receipt_items",
    )
    item_name = models.CharField(max_length=255)
    price = models.IntegerField()
    detection_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "RECEIPT_ITEMS"
        managed = False
