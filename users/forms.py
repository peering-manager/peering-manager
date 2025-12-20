from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from peering.models import AutonomousSystem
from utils.forms import BootstrapMixin
from utils.forms.fields import DynamicModelChoiceField
from utils.forms.utils import add_blank_choice
from utils.forms.widgets import StaticSelect

from .models import Token

__all__ = ("LoginForm", "TokenForm", "UserPasswordChangeForm", "UserPreferencesForm")


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


class UserPreferencesForm(BootstrapMixin, forms.Form):
    context_as = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        required=False,
        label="Context AS",
        help_text="Select the affiliated AS to use as your context.<br><code>context.as</code>",
    )
    page_length = forms.ChoiceField(
        required=False,
        label="Page length",
        help_text=f"Number of items to display per page (default: {settings.PAGINATE_COUNT}).<br><code>pagination.per_page</code>",
        widget=StaticSelect(),
    )
    config_context_format = forms.ChoiceField(
        required=False,
        choices=add_blank_choice([("json", "JSON"), ("yaml", "YAML")]),
        label="Config context format",
        help_text="Preferred format for displaying configuration context.<br><code>configcontext.format</code>",
        widget=StaticSelect(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        page_lengths = [25, 50, 100, 250, 500, 1000]

        if settings.PAGINATE_COUNT not in page_lengths:
            page_lengths.append(settings.PAGINATE_COUNT)
            page_lengths.sort()

        self.fields["page_length"].choices = add_blank_choice(
            [(str(n), str(n)) for n in page_lengths]
        )
