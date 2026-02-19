from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    # PK（BigAutoFieldで統一）
    id = models.BigAutoField(primary_key=True)

    # email login（AbstractUserの username ログインを使わず email をログインIDにする）
    email = models.EmailField(unique=True)

    # profile（S3などのURLを保存する）
    image_url = models.CharField(max_length=2048, null=True, blank=True)

    # Googleログイン用のUID（Google連携しない場合はNULL）
    google_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)

    # created_at / updated_at（監査用）
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ログインIDに email を使う
    USERNAME_FIELD = "email"
    # createsuperuser 等で必須入力にするフィールド
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "USERS"


# 共有グループ
class ShareGroup(models.Model):

    id = models.BigAutoField(primary_key=True)

    # グループ名（同じ作成者の中では重複不可にする）
    name = models.CharField(max_length=255)

    # グループを作成したユーザー（管理者的な扱い）
    # PROTECT: 作成者ユーザーを消すとグループが壊れるので削除を止める
    created_by_user = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        db_column="created_by_user_id",
        related_name="created_share_groups",
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "SHARE_GROUPS"
        constraints = [
            # 「同じ作成者が同名グループを作れない」制約
            models.UniqueConstraint(
                fields=["created_by_user", "name"],
                name="uq_sharegroup_createdby_name",
            ),
        ]

# グループ所属ユーザー（中間テーブル）
class ShareGroupMember(models.Model):

    id = models.BigAutoField(primary_key=True)

    # どのグループに所属しているか
    # CASCADE: グループ削除時は所属情報も不要なので一緒に削除
    share_group = models.ForeignKey(
        "ShareGroup",
        on_delete=models.CASCADE,
        db_column="share_group_id",
        related_name="member_links",
    )

    # 誰が所属しているか
    # CASCADE: ユーザー削除時は所属情報も不要なので一緒に削除
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="share_group_links",
    )

    # 役割（MVPでは owner / member 程度）
    role = models.CharField(max_length=10, default="member")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "SHARE_GROUP_MEMBERS"
        constraints = [
            # 同じユーザーが同じグループに重複所属できない
            models.UniqueConstraint(
                fields=["share_group", "user"],
                name="uq_share_group_members_group_user",
            )
        ]

# カテゴリ（支出/収入の分類）
class Category(models.Model):

    id = models.BigAutoField(primary_key=True)

    # ユーザー個別カテゴリ
    # SET_NULL: ユーザー削除時にカテゴリごと消すのではなく、NULLにして残す（要件次第）
    user = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        db_column="user_id",
        null=True,
        blank=True,
        related_name="categories",
    )

    # グループ共通カテゴリ（将来用 / 互換用）
    group = models.ForeignKey(
        "ShareGroup",
        on_delete=models.SET_NULL,
        db_column="group_id",
        null=True,
        blank=True,
        related_name="categories",
    )

    # カテゴリ名（例: 食費、娯楽、給料）
    name = models.CharField(max_length=255)

    # 色（#RRGGBB 形式のみ許可）
    color = models.CharField(
        max_length=7,
        validators=[RegexValidator(regex=r"^#[0-9A-Fa-f]{6}$")],
    )

    # 収入カテゴリなら True、支出カテゴリなら False
    is_in_type = models.BooleanField()

    # フロントで使うアイコンキー（例: "food", "salary"）
    icon_key = models.CharField(max_length=50)

    # デフォルトカテゴリかどうか（seedで作るものなど）
    is_builtin = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CATEGORIES"
        constraints = [
            # ユーザー単位でカテゴリ名をユニークにする
            models.UniqueConstraint(
                fields=["user", "name"],
                name="uq_category_user_name",
            ),
            # グループ単位でカテゴリ名をユニークにする（グループ共通カテゴリ用）
            models.UniqueConstraint(
                fields=["group", "name"],
                name="uq_category_group_name",
            ),
        ]

# 収支データ
class MoneyFlow(models.Model):

    id = models.BigAutoField(primary_key=True)

    # どのカテゴリの収支か
    # PROTECT: 過去データを壊すのでカテゴリ削除を防ぐ
    category = models.ForeignKey(
        "Category",
        on_delete=models.PROTECT,
        db_column="category_id",
        related_name="money_flows",
    )

    # レシート連携用（未使用ならNULL）
    receipt_id = models.BigIntegerField(null=True, blank=True)

    # 金額（整数円）
    amount = models.DecimalField(max_digits=10, decimal_places=0)

    # 日付（支出/収入が発生した日）
    expense_date = models.DateField()

    # メモ（任意）
    memo = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "MONEY_FLOWS"
