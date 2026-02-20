from .models import Category


DEFAULT_CATEGORY_SPECS = [
    # 支出（is_in_type=False）
    ("食費", False, "food", "#FFB44F"),
    ("住居費", False, "home", "#E1BFFF"),
    ("交通費", False, "transport", "#62B2FD"),
    ("光熱費", False, "utilities", "#9BDFC4"),
    ("娯楽", False, "fun", "#F99BAB"),
    ("洋服", False, "clothes", "#FFC6D7"),
    ("医療費", False, "medical", "#9F97F7"),
    ("日用品", False, "daily", "#AEE3F5"),
    ("支出その他", False, "other_exp", "#86BE63"),
    # 収入（is_in_type=True）
    ("給料", True, "salary", "#FACC15"),
    ("収入その他", True, "other_inc", "#FFD5D2"),
]


def create_default_categories(user):
    categories = [
        Category(
            user=user,              # このカテゴリを所有するユーザー
            group=None,             # 個人用カテゴリ
            name=name,              # カテゴリ名
            color=color_hex,        # 表示カラー
            is_in_type=is_in_type,  # 収入(True) / 支出(False)
            icon_key=icon_key,      # フロント用アイコンキー
            is_builtin=True,        # 初期カテゴリであることを示すフラグ
        )
        for name, is_in_type, icon_key, color_hex in DEFAULT_CATEGORY_SPECS
    ]
    Category.objects.bulk_create(categories)
