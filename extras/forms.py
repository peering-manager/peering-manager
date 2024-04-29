from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from requests.exceptions import HTTPError

from utils.forms import BOOLEAN_WITH_BLANK_CHOICES, BootstrapMixin, BulkEditForm
from utils.forms.fields import (
    ContentTypeChoiceField,
    ContentTypeMultipleChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    SlugField,
    TemplateField,
)
from utils.forms.widgets import (
    APISelectMultiple,
    ColourSelect,
    StaticSelect,
    StaticSelectMultiple,
)

from .enums import HttpMethod, ObjectChangeAction
from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    ObjectChange,
    Tag,
    Webhook,
)
from .utils import FeatureQuery


class ConfigContextForm(BootstrapMixin, forms.ModelForm):
    data = JSONField()
    fieldsets = (
        ("Config Context", ("name", "description", "is_active")),
        ("Data", ("data",)),
        ("Data Source", ("data_source", "data_file", "auto_synchronisation_enabled")),
    )

    class Meta:
        model = ConfigContext
        fields = "__all__"

    def clean(self):
        if not self.cleaned_data["data"] and not self.cleaned_data["data_file"]:
            raise ValidationError(
                "Either data or a file from a data source must be provided"
            )
        return super().clean()


class ConfigContextFilterForm(BootstrapMixin, forms.Form):
    model = ConfigContext
    q = forms.CharField(required=False, label="Search")
    is_active = forms.NullBooleanField(
        required=False,
        label="Active",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )


class ConfigContextAssignmentForm(BootstrapMixin, forms.ModelForm):
    config_context = DynamicModelChoiceField(
        queryset=ConfigContext.objects.filter(is_active=True)
    )

    class Meta:
        model = ConfigContextAssignment
        fields = ("config_context", "weight")


class ExportTemplateForm(BootstrapMixin, forms.ModelForm):
    template = TemplateField(required=False)
    content_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=FeatureQuery("export-templates"),
        label="Object type",
    )
    fieldsets = (
        (
            "Export Template",
            (
                "name",
                "content_type",
                "description",
                "jinja2_trim",
                "jinja2_lstrip",
                "template",
            ),
        ),
        ("Data Source", ("data_source", "data_file", "auto_synchronisation_enabled")),
    )

    class Meta:
        model = ExportTemplate
        fields = "__all__"
        widgets = {
            "template": forms.Textarea(attrs={"class": "text-monospace"}),
        }

    def clean(self):
        if not self.cleaned_data["template"] and not self.cleaned_data["data_file"]:
            raise ValidationError(
                "Either the template code or a file from a data source must be provided"
            )
        return super().clean()


class ExportTemplateFilterForm(BootstrapMixin, forms.Form):
    model = ExportTemplate
    q = forms.CharField(required=False, label="Search")


class IXAPIForm(BootstrapMixin, forms.ModelForm):
    identity = forms.CharField(widget=StaticSelect)
    fieldsets = (("IX-API", ("name", "url", "api_key", "api_secret", "identity")),)

    class Meta:
        model = IXAPI
        fields = ("name", "url", "api_key", "api_secret", "identity")

    def clean(self):
        cleaned_data = super().clean()

        try:
            # Try to query API and see if it raises an error
            IXAPI.test_connectivity(
                cleaned_data["url"], cleaned_data["api_key"], cleaned_data["api_secret"]
            )
        except HTTPError as e1:
            # Fail form validation on HTTP error to provide a feedback to the user
            if e1.response.status_code >= 400 and e1.response.status_code < 500:
                possible_issue = "make sure the URL, key and secret are correct"
            else:
                possible_issue = "the server is malfunctioning or unavailable"
            raise ValidationError(
                f"Unable to connect to IX-API ({e1.response.status_code} {e1.response.reason}), {possible_issue}."
            ) from e1
        except Exception as e2:
            # Raised by pyixapi
            raise ValidationError(str(e2)) from e2


class IXAPIFilterForm(BootstrapMixin, forms.Form):
    model = IXAPI
    q = forms.CharField(required=False, label="Search")


class ObjectChangeFilterForm(BootstrapMixin, forms.Form):
    model = ObjectChange
    q = forms.CharField(required=False, label="Search")
    time_after = forms.DateTimeField(
        label="After",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "YYYY-MM-DD hh:mm:ss"}),
    )
    time_before = forms.DateTimeField(
        label="Before",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "YYYY-MM-DD hh:mm:ss"}),
    )
    action = forms.ChoiceField(
        required=False, choices=ObjectChangeAction, widget=StaticSelectMultiple
    )
    user_id = DynamicModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        display_field="username",
        label="User",
        widget=APISelectMultiple(api_url="/api/users/users/"),
    )


class TagBulkEditForm(BulkEditForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), widget=forms.MultipleHiddenInput
    )
    color = forms.CharField(max_length=6, required=False, widget=ColourSelect())

    model = Tag
    nullable_fields = ["comments"]


class TagFilterForm(BootstrapMixin, forms.Form):
    model = Tag
    q = forms.CharField(required=False, label="Search")


class TagForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()

    fieldsets = (("Tag", ("name", "slug", "color", "description")),)

    class Meta:
        model = Tag
        fields = ["name", "slug", "color", "description"]


class WebhookForm(BootstrapMixin, forms.ModelForm):
    content_types = ContentTypeMultipleChoiceField(
        queryset=ContentType.objects.all(), limit_choices_to=FeatureQuery("webhooks")
    )
    http_method = forms.ChoiceField(
        choices=HttpMethod, widget=StaticSelect, label="HTTP method"
    )

    fieldsets = (
        ("Webhook", ("name", "content_types", "enabled")),
        ("Events", ("type_create", "type_update", "type_delete")),
        (
            "HTTP Request",
            (
                "payload_url",
                "http_method",
                "http_content_type",
                "additional_headers",
                "body_template",
                "secret",
            ),
        ),
        ("Conditions", ("conditions",)),
        ("SSL", ("ssl_verification", "ca_file_path")),
    )

    class Meta:
        model = Webhook
        fields = "__all__"
        labels = {
            "type_create": "Creations",
            "type_update": "Updates",
            "type_delete": "Deletions",
        }
        widgets = {
            "additional_headers": forms.Textarea(attrs={"class": "text-monospace"}),
            "body_template": forms.Textarea(attrs={"class": "text-monospace"}),
            "conditions": forms.Textarea(attrs={"class": "text-monospace"}),
        }


class WebhookFilterForm(BootstrapMixin, forms.Form):
    model = Webhook
    content_type_id = ContentTypeMultipleChoiceField(
        queryset=ContentType.objects.filter(FeatureQuery("webhooks").get_query()),
        required=False,
        label="Object type",
    )
    http_method = forms.MultipleChoiceField(
        required=False,
        choices=HttpMethod,
        widget=StaticSelectMultiple,
        label="HTTP method",
    )
    enabled = forms.NullBooleanField(
        required=False, widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )
    type_create = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
        label="Object creations",
    )
    type_update = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
        label="Object updates",
    )
    type_delete = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
        label="Object deletions",
    )
