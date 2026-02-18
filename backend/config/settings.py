from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "1") == "1"

# "localhost,127.0.0.1" みたいに env で渡したのを分割
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",   #google認証機能　

    "allauth", #ログイン,ログアウト
    "allauth.account", #メールパスワード
    "allauth.socialaccount", #Googleから帰ってきた情報を受け取る
    "allauth.socialaccount.providers.google", #googleのurlを使用する

    "django_browser_reload",
    "web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "allauth.account.middleware.AccountMiddleware", #google認証

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
    
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # web/templates をプロジェクト直下に置いているので DIRS で拾う
        "DIRS": [BASE_DIR / "web" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---- DB (MySQL) ----
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", os.getenv("MYSQL_DATABASE", "")),
        "USER": os.getenv("DB_USER", os.getenv("MYSQL_USER", "")),
        "PASSWORD": os.getenv("DB_PASSWORD", os.getenv("MYSQL_PASSWORD", "")),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# ---- AUTH(認証関連) ----
AUTH_USER_MODEL = "web.User"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

# ---- Static ----
STATIC_URL = "/static/"
# 本番で collectstatic する時の出力先
STATIC_ROOT = BASE_DIR / "staticfiles"

# staticは web/static以下で統一
STATICFILES_DIRS = [
    BASE_DIR / "web" / "static",  # css はここ
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

#google認証に必要なコード
SITE_ID = 1       # 1=localhost:8000
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend", #djangoの標準認証
    "allauth.account.auth_backends.AuthenticationBackend", #外部認証を認める

]
SOCIALACCOUNT_LOGIN_ON_GET = True

# 画像をアップロード
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

