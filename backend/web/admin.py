from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ShareGroup, Category, Receipt, MoneyFlow

class UserAdmin(BaseUserAdmin):
    ordering = ('id',)
    list_display = ("email", "name", "is_staff", "is_active")

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'icon', 'group')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'is_staff',
                'is_superuser',
            ),
        }),
    )

    search_fields = ('email', 'name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')

admin.site.register(User, UserAdmin)
admin.site.register(ShareGroup)
admin.site.register(Category)
admin.site.register(Receipt)
admin.site.register(MoneyFlow)