from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.postgres.forms import SimpleArrayField

from peering.models import AutonomousSystem
from utils.forms import BootstrapMixin
from utils.forms.fields import DynamicModelChoiceField, IPNetworkFormField
from utils.forms.utils import add_blank_choice
from utils.forms.widgets import DateTimePicker, StaticSelect

from .models import Token, TokenObjectPermission

__all__ = ("LoginForm", "TokenForm", "TokenObjectPermissionForm", "UserPasswordChangeForm", "UserPreferencesForm")


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
        fields = ["key", "write_enabled", "can_manage_permissions", "expires", "description", "allowed_ips"]
        widgets = {"expires": DateTimePicker()}
        help_texts = 
            "can_manage_permissions": "Allow this token to manage token object permissions via API",
        }


class TokenObjectPermissionForm(BootstrapMixin, forms.ModelForm):
    """
    Generic form for creating/editing token object permissions.

    Accepts custom actions dynamically via available_actions parameter.
    Can be used for any object type (Router, AutonomousSystem, etc.).
    """

    token = forms.ModelChoiceField(
        queryset=Token.objects.select_related("user").all(),
        required=True,
        help_text="Select the API token to grant or restrict permissions for",
    )

    class Meta:
        model = TokenObjectPermission
        fields = ["token", "can_view", "can_edit", "can_delete"]
        help_texts = {
            "can_view": "Allow viewing this object's details (GET requests)",
            "can_edit": "Allow modifying this object's settings (PATCH/PUT requests)",
            "can_delete": "Allow deleting this object (DELETE requests)",
        }
        widgets = {
            "content_type": forms.HiddenInput(),
            "object_id": forms.HiddenInput(),
        }

    def __init__(self, *args, available_actions=None, **kwargs):
        """
        Initialize the form with optional custom actions.

        Args:
            available_actions: Dict of {action_name: {label, help_text}} for custom actions
                Example: {
                    "configure": {
                        "label": "Allow: Deploy Configuration",
                        "help_text": "Allow deploying configuration"
                    }
                }
        """
        super().__init__(*args, **kwargs)

        self.available_actions = available_actions or {}
        self.action_fields = []

        # Dynamically create checkbox fields for each available action
        for action_name, action_config in self.available_actions.items():
            field_name = f"action_{action_name}"
            self.action_fields.append((action_name, field_name))

            # Get initial value from existing permission or default to False
            initial_value = False
            if self.instance and self.instance.pk:
                custom_actions = self.instance.custom_actions or {}
                initial_value = custom_actions.get(action_name, False)

            # Create the checkbox field
            self.fields[field_name] = forms.BooleanField(
                required=False,
                initial=initial_value,
                label=action_config.get(
                    "label", f"Allow: {action_name.replace('_', ' ').title()}"
                ),
                help_text=action_config.get("help_text", f"Allow {action_name} action"),
            )

    def save(self, commit=True):
        """Build custom_actions from dynamically created checkbox fields."""
        instance = super().save(commit=False)

        # Build custom_actions dict from action checkbox fields
        instance.custom_actions = {}
        for action_name, field_name in self.action_fields:
            instance.custom_actions[action_name] = self.cleaned_data.get(
                field_name, False
            )

        if commit:
            instance.save()

        return instance
        


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
