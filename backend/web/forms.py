from django.contrib.auth.forms import UserCreationForm
from .models import User

class EmailUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["email", "password1", "password2"]  

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data["email"] or "").strip().lower()
        user.username = user.email  
        if commit:
            user.save()
        return user
