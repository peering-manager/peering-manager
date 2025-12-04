from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from utils.forms import BootstrapMixin

from .models import Token, TokenObjectPermission

__all__ = (
    "LoginForm",
    "TokenForm",
    "TokenObjectPermissionForm",
    "UserPasswordChangeForm",
)


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
        fields = [
            "key",
            "write_enabled",
            "can_manage_permissions",
            "expires",
            "description",
        ]
        help_texts = {
            "expires": "YYYY-MM-DD [HH:MM:SS]",
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
