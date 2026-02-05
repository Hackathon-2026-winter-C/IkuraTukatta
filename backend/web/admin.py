from django.contrib import admin
from .models import User, ShareGroup, Category, Receipt, MoneyFlow

admin.site.register(User)
admin.site.register(ShareGroup)
admin.site.register(Category)
admin.site.register(Receipt)
admin.site.register(MoneyFlow)