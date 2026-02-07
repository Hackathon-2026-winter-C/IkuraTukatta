from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_staff")
    fields = (
        "email",
        "name",
        "icon",
        "is_staff",
        "is_active",
        "password",
    )