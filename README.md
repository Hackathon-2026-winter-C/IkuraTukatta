# 初期ファイル構成

```text
/
├── backend
│   ├── config
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   ├── scripts
│   │   └── entrypoint.sh    #python manage.pyの実行ファイル
│   └── web
│       ├── apps.py
│       ├── models.py        #DB構成変わると変える必要あり
│       ├── static
│       ├── templates
│       ├── theme
│       ├── urls.py          #urlの定義
│       └── views.py
├── CチームER図.drawio
├── db
│   └── init
│       ├── schema.sql       #ER図からDB構成
│       └── seed.sql         #ダミーデータ
├── docker-compose.yml
├── infra                    #AWS(Terraform)
└── README.md
```

# docker 立ち上げ方

## ①.env.sample から.env を作成

```bash
ディレクトリルートで実行
cp .env.sample .env
```

### .env に access_key と secret_access_key を記述

```text
AWS_S3_REGION_NAME=ap-northeast-1
AWS_STORAGE_BUCKET_NAME=hackathon-media-s3-bucket-20260207
AWS_ACCESS_KEY_ID=  配布されたaccess_keyを入れる
AWS_SECRET_ACCESS_KEY=　配布されたsecret_access_keyを入れる
```

## ②

```bash
ディレクトリルートで実行
docker compose up --build
```

## ③

docker を削除する場合(-v をつけると volume も削除されます)

```bash
ディレクトリルートで実行
docker compose down -v
```

# アクセス方法

```text
http://localhost:8000/
http://localhost:8000/charts
http://localhost:8000/dashboard

http://localhost:8000/api/users
↑テストで作成
```

# Django Template でフォーマッターが邪魔する場合

以下プラグインのインストール
Unibeautify - Universal Formatter

ディレクトリルートで.vscode/settings.json を作成

```json:settings.json
{
  "files.associations": {
    "**/templates/**/*.html": "django-html"
  },
  "emmet.includeLanguages": {
    "django-html": "html",
    "django": "html"
  },
  "emmet.showExpandedAbbreviation": "always",
  "emmet.triggerExpansionOnTab": true,
  "editor.quickSuggestions": {
    "other": true,
    "comments": false,
    "strings": true
  },
  "html.autoClosingTags": true
}
```




# セキュリティ対策

1. SQLインジェクション対策
Django ORMを使用し、SQLを直接記述しないことで、ユーザー入力がSQL文として実行されることを防止している。

  # views.py などで ORM を利用
  Models.object,filter(field=value)


2. CSRF対策
DjangoのCSRFミドルウェアとテンプレートのトークン機構利用し、不正なPOSTリクエストを防止している。

  # settings.py
  MIDDLEWARE = [
    "django.middlewere.csrf.CsrfViwe.Middleware",
  ]

  # html
  <form method="post>
    {% csrf_token %}
  </form>


3. XSS対策
Djangoテンプレートの自動エスケープ気候により、ユーザー入力がHTMLやJavaScriptとして実行されることを防止している。

  {{ user_input }}   <!-- 自動的にエスケープされる -->

  # settings.py
  SECURE_CONTENT_TYPE_NOSNIFF = True


4. クリックジャッキング対策
X_Frame-Optionsヘッダを付与し、外部サイトからiframeで埋め込まれることを防止している。

  # settings.py
  X_FRAME_OPTIONS = "DENY"

  MIDDLEWARE = [
    "django.middleware.clickjacking.XframeMiddleware",
  ]

5. CORS対策
フロントエンドとバックエンドを同一オリジンで運用し、外部オリジンからのアクセスを許可していない。


