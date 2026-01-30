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

## ②

```bash
ディレクトリルートで実行
docker compose up --build
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
