from django.urls import path
from . import views

urlpatterns = [
    path("", views.index_page, name="index"),
    path("settings", views.settings_page, name="settings"),
    path("user", views.user_page, name="user"),
    path("charts", views.charts_page, name="charts"),
    path("dashboard/",views.dashboard_page, name="dashboard"),
    path('accounts/signup/', views.signup_view, name='signup'),

    path("api/users", views.users_api, name="users_api")
]