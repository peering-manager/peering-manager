from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from utils.forms import BootstrapMixin

from .models import Token

__all__ = ("LoginForm", "TokenForm", "UserPasswordChangeForm")


class LoginForm(BootstrapMixin, AuthenticationForm):
    pass


class UserPasswordChangeForm(BootstrapMixin, PasswordChangeForm):
    pass


class TokenForm(BootstrapMixin, forms.ModelForm):
    key = forms.CharField(
        required=False,
        help_text="If no key is provided, one will be generated automatically.",
    )

    class Meta:
        model = Token
        fields = ["key", "write_enabled", "expires", "description"]
        help_texts = {"expires": "YYYY-MM-DD [HH:MM:SS]"}
