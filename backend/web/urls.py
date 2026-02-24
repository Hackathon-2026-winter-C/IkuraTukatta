# backend/web/urls.py
from django.urls import path
from . import views

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 開発
    path("", views.index_page, name="index"),
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("signup/theme/", views.signup_theme_choice_page, name="signup_theme_choice"),
    path("auth/google/", views.google_login_api, name="google_login_api"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_page, name="dashboard"),
    path("dashboard/charts/", views.charts_page, name="charts"),
    path("dashboard/list/", views.dashboard_list_page, name="dashboard_list"),
    path(
        "dashboard/moneyflow/form/",
        views.dashboard_moneyflow_form_page,
        name="dashboard_moneyflow_form",
    ),
    path(
        "dashboard/moneyflow/edit/",
        views.dashboard_moneyflow_edit_page,
        name="dashboard_moneyflow_edit",
    ),
    path(
    "dashboard/moneyflow/delete/",
    views.dashboard_moneyflow_delete_page,
    name="dashboard_moneyflow_delete",
    ),

    path(
        "dashboard/moneyflow/category/",
        views.dashboard_moneyflow_category_page,
        name="dashboard_moneyflow_category",
    ),
    path("dashboard/account/", views.account_page, name="account"),
    path("account/edit/", views.account_edit, name="account_edit"),

    # APIs
    path("api/categories/create/", views.category_create_api, name="category_create_api"),
    path(
        "api/categories/<int:category_id>/rename/",
        views.category_rename_api,
        name="category_rename_api",
    ),
    path(
        "api/categories/<int:category_id>/delete/",
        views.category_delete_api,
        name="category_delete_api",
    ),
    path("api/users", views.users_api, name="users_api"),

    # レシートテスト用
    path("receipt_test/", views.receipt_test_page),
    path("receipt_upload_api", views.receipt_upload_api),
    path("receipt_save_api", views.receipt_save_api),

    # path("dashboard/date/", views.dashboard_date_page, name="dashboard_date"), #
    path("account/share", views.share_page, name="share"),
    path("account/group/create", views.group_create, name="group_create"),

    

    
    # テストAPI
    # path("api/users", views.users_api, name="users_api")
]
