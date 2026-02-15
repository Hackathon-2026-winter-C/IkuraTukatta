from django.urls import path
from . import views

urlpatterns = [
    # 開発
    path("", views.index_page, name="index"),
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("logout", views.logout_view, name="logout"),

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

    # 既存API
    path("api/categories/create/", views.category_create_api, name="category_create_api"),
    path("api/categories/<int:category_id>/rename/", views.category_rename_api, name="category_rename_api"),
    path("api/categories/<int:category_id>/delete/", views.category_delete_api, name="category_delete_api"),
    path("api/users/", views.users_api, name="users_api"),

    # ===== Ledger Share APIs =====
    path("api/ledger/available/", views.ledger_available_api, name="ledger_available_api"),
    path("api/ledger/select/", views.ledger_select_api, name="ledger_select_api"),

    path("api/ledger/share/add/", views.ledger_share_add_api, name="ledger_share_add_api"),
    path("api/ledger/share/list/", views.ledger_share_list_api, name="ledger_share_list_api"),
    path("api/ledger/share/remove/", views.ledger_share_remove_api, name="ledger_share_remove_api"),
]
