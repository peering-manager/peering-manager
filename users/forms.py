from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.postgres.forms import SimpleArrayField

from peering.models import AutonomousSystem
from utils.forms import BootstrapMixin
from utils.forms.fields import DynamicModelChoiceField, IPNetworkFormField
from utils.forms.utils import add_blank_choice
from utils.forms.widgets import DateTimePicker, StaticSelect

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
    allowed_ips = SimpleArrayField(
        base_field=IPNetworkFormField(),
        required=False,
        label="Allowed IPs",
        help_text=(
            "Allowed IPv4/IPv6 networks from where the token can be used. Leave blank for no restrictions. "
            "Example: <kbd>10.1.1.0/24,192.168.10.16/32,2001:db8:1::/64</kbd>"
        ),
    )

    class Meta:
        model = Token
        fields = ["key", "write_enabled", "expires", "description", "allowed_ips"]
        widgets = {"expires": DateTimePicker()}


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
