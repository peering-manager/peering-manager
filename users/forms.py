from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from .models import Token
from peering.models import AutonomousSystem
from utils.forms import BootstrapMixin, DynamicModelChoiceField


class LoginForm(BootstrapMixin, AuthenticationForm):
    """
    Bootstraped login form.
    """

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        self.fields["username"].widget.attrs["placeholder"] = ""
        self.fields["password"].widget.attrs["placeholder"] = ""


class UserPreferredASChangeForm(BootstrapMixin, forms.Form):
    preferred_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Preferred Autonomous System",
    )


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
