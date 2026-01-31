from django.urls import path
from . import views
from .views import login_view

urlpatterns = [
    # テスト
    path("", views.index_page, name="index"),
    path("settings", views.settings_page, name="settings"),
    path("user", views.user_page, name="user"),
    # path("charts", views.charts_page, name="charts"),
    # path("dashboard/",views.dashboard_page, name="dashboard"),
    path("test-footer/", views.test_footer_page, name="test_footer"),

    # 開発
    path("login/", views.login_view, name="login"),
    path("signup", views.signup_page, name="signup"),
    path("dashboard/",views.dashboard_page, name="dashboard"),
    path("dashboard/charts", views.charts_page, name="charts"),
    path("dashboard/list", views.dashboard_list_page, name="dashboard_list"),
    path("dashboard/moneyflow/form", views.dashboard_moneyflow_form_page, name="dashboard_moneyflow_form"),
    path("dashboard/moneyflow/edit", views.dashboard_moneyflow_edit_page, name="dashboard_moneyflow_edit"),
    path("dashboard/moneyflow/category", views.dashboard_moneyflow_category_page, name="dashboard_moneyflow_category"),
    path("dashboard/account", views.account_page, name="account"),
    path("whoami/", views.whoami, name="whoami"),


    # テストAPI
    path("api/users", views.users_api, name="users_api")
]