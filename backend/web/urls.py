
from django.urls import path

from . import views

urlpatterns = [
    # テスト
    # path("", views.index_page, name="index"),
    # path("settings", views.settings_page, name="settings"),
    # path("user", views.user_page, name="user"),
    # path("charts", views.charts_page, name="charts"),
    # path("dashboard/",views.dashboard_page, name="dashboard"),
    # path("test-footer/", views.test_footer_page, name="test_footer"),

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

    # API
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
    path(
        "api/account/username/",
        views.account_username_update_api,
        name="account_username_update_api",
    ),
    path(
        "api/account/email/",
        views.account_user_email_update_api,
        name="account_user_email_update_api",
    ),
    path(
        "api/account/password/",
        views.account_user_password_update_api,
        name="account_user_password_update_api",
    ),
    path("api/account/profile-image/", views.profile_image_update_api, name="profile_image_update_api"),
    path("api/users", views.users_api, name="users_api"),

    # # レシートテスト用
    # path("receipt_test/", views.receipt_test_page),
    # path("receipt_upload_api", views.receipt_upload_api),
    # path("receipt_save_api", views.receipt_save_api),
    
    path("api/categories/<int:category_id>/rename/", views.category_rename_api, name="category_rename_api"),
    path("api/categories/<int:category_id>/delete/", views.category_delete_api, name="category_delete_api"),
    path("api/users/", views.users_api, name="users_api"),
    path("api/account/delete/", views.account_delete_api, name="account_delete_api"),
    path("api/account/theme-choice/complete/", views.signup_theme_choice_complete_api, name="signup_theme_choice_complete_api"),
    path("api/receipts/analyze/", views.receipt_analyze_api, name="receipt_analyze_api"),
    path("api/charts/data/", views.charts_data_api, name="charts_data_api"),

    # ===== 共有 APIs  =====
    path("api/groups/available/", views.groups_available_api, name="groups_available_api"),
    path("api/groups/select/", views.groups_select_api, name="groups_select_api"),
    path("api/groups/create/", views.groups_create_api, name="groups_create_api"),
    path("api/groups/<int:group_id>/members/", views.groups_members_list_api, name="groups_members_list_api"),
    path("api/groups/<int:group_id>/members/add/", views.groups_members_add_api, name="groups_members_add_api"),
    path("api/groups/<int:group_id>/members/remove/", views.groups_members_remove_api, name="groups_members_remove_api"),
    path("api/groups/<int:group_id>/delete/", views.groups_delete_api, name="groups_delete_api"),
]
