from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class EmailUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["email", "password1", "password2"]


# UserUpdateForm
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "image_url"]
