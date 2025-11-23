from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from taggit.forms import TagField

from bgp.models import Community
from core.forms import PushedDataMixin, SynchronisedDataMixin
from extras.netbox import NetBox
from peering.models import AutonomousSystem
from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from peering_manager.forms.base import PeeringManagerModelBulkEditForm
from utils.forms import BOOLEAN_WITH_BLANK_CHOICES, add_blank_choice
from utils.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    PasswordField,
    SlugField,
    TagFilterField,
    TemplateField,
)
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from .enums import DeviceStatus, PasswordAlgorithm
from .models import Configuration, Platform, Router

__all__ = ("ConfigurationFilterForm", "ConfigurationForm", "PlatformForm", "RouterForm")


class ConfigurationForm(PeeringManagerModelForm, SynchronisedDataMixin):
    template = TemplateField(required=False)
    comments = CommentField()
    tags = TagField(required=False)
    fieldsets = (
        (
            "Configuration",
            ("name", "description", "jinja2_trim", "jinja2_lstrip", "template"),
        ),
        ("Data Source", ("data_source", "data_file", "auto_synchronisation_enabled")),
    )

    class Meta:
        model = Configuration
        fields = (
            "name",
            "description",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
            "data_source",
            "data_file",
            "auto_synchronisation_enabled",
        )

    def clean(self):
        if not self.cleaned_data["template"] and not self.cleaned_data["data_file"]:
            raise ValidationError(
                "Either the template code or a file from a data source must be provided"
            )
        return super().clean()


class ConfigurationFilterForm(PeeringManagerModelFilterSetForm):
    model = Configuration
    tag = TagFilterField(model)


class PlatformForm(PeeringManagerModelForm):
    slug = SlugField(max_length=255)
    password_algorithm = forms.ChoiceField(
        required=False, choices=add_blank_choice(PasswordAlgorithm), widget=StaticSelect
    )
    napalm_args = JSONField(
        required=False,
        label="Optional arguments",
        help_text="See NAPALM's <a href='http://napalm.readthedocs.io/en/latest/support/#optional-arguments'>documentation</a> for a complete list of optional arguments",
    )
    tags = TagField(required=False)
    fieldsets = (
        (
            "Platform",
            (
                "name",
                "slug",
                "description",
                "password_algorithm",
                "napalm_driver",
                "napalm_args",
            ),
        ),
    )

    class Meta:
        model = Platform
        fields = (
            "name",
            "slug",
            "description",
            "password_algorithm",
            "napalm_driver",
            "napalm_args",
            "tags",
        )


class RouterForm(PushedDataMixin, PeeringManagerModelForm):
    netbox_device_id = forms.IntegerField(required=False, label="NetBox device")
    platform = DynamicModelChoiceField(required=False, queryset=Platform.objects.all())
    status = forms.ChoiceField(
        required=False, choices=DeviceStatus, widget=StaticSelect
    )
    configuration_template = DynamicModelChoiceField(
        required=False,
        queryset=Configuration.objects.all(),
        label="Configuration",
        help_text="Template used to generate device configuration",
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    local_context_data = JSONField(required=False)
    napalm_username = forms.CharField(required=False, label="Username")
    napalm_password = PasswordField(required=False, render_value=True, label="Password")
    napalm_timeout = forms.IntegerField(
        required=False,
        label="Timeout",
        help_text="The maximum time to wait for a connection in seconds",
    )
    napalm_args = JSONField(
        required=False,
        label="Optional arguments",
        help_text="See NAPALM's <a href='http://napalm.readthedocs.io/en/latest/support/#optional-arguments'>documentation</a> for a complete list of optional arguments",
    )
    comments = CommentField()
    tags = TagField(required=False)
    fieldsets = (
        (
            "Router",
            (
                "name",
                "hostname",
                "encrypt_passwords",
                "poll_bgp_sessions_state",
                "configuration_template",
                "local_autonomous_system",
                "netbox_device_id",
            ),
        ),
        ("Management", ("platform", "status")),
        (
            "NAPALM",
            ("napalm_username", "napalm_password", "napalm_timeout", "napalm_args"),
        ),
        ("Data Source", ("data_source", "data_path")),
        ("Config Context", ("local_context_data",)),
        ("Policy Options", ("communities",)),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings.NETBOX_API:
            choices = []
            for device in NetBox().get_devices():
                try:
                    choices.append((device.id, device.display))
                except AttributeError:
                    # Fallback to hold API attribute
                    choices.append((device.id, device.display_name))

            self.fields["netbox_device_id"] = forms.ChoiceField(
                required=False,
                label="NetBox device",
                choices=[(0, "---------"), *choices],
                widget=StaticSelect,
            )
            self.fields["netbox_device_id"].widget.attrs["class"] = " ".join(
                [
                    self.fields["netbox_device_id"].widget.attrs.get("class", ""),
                    "form-control",
                ]
            ).strip()
        else:
            self.fields["netbox_device_id"].widget = forms.HiddenInput()

    class Meta:
        model = Router

        fields = (
            "netbox_device_id",
            "name",
            "hostname",
            "platform",
            "status",
            "encrypt_passwords",
            "poll_bgp_sessions_state",
            "configuration_template",
            "local_autonomous_system",
            "local_context_data",
            "napalm_username",
            "napalm_password",
            "napalm_timeout",
            "napalm_args",
            "communities",
            "comments",
            "tags",
            "data_source",
            "data_path",
        )
        help_texts = {"hostname": "Router hostname (must be resolvable) or IP address"}


class RouterBulkEditForm(PeeringManagerModelBulkEditForm):
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    platform = DynamicModelChoiceField(required=False, queryset=Platform.objects.all())
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(DeviceStatus),
        widget=StaticSelect,
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    poll_bgp_sessions_state = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
        label="Poll BGP sessions state",
    )
    configuration_template = DynamicModelChoiceField(
        required=False, queryset=Configuration.objects.all()
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_context_data = JSONField(required=False)
    comments = CommentField()

    model = Router
    nullable_fields = ("communities", "local_context_data", "comments")


class RouterFilterForm(PeeringManagerModelFilterSetForm):
    model = Router
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    platform_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Platform.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Platform",
    )
    status = forms.MultipleChoiceField(
        required=False, choices=DeviceStatus, widget=StaticSelectMultiple
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    configuration_template_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Configuration.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Configuration",
    )
    tag = TagFilterField(model)
