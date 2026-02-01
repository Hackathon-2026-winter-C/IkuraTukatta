from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

# UserCreationFormを拡張
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "password1", "password2"]