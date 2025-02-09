from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from requests.exceptions import HTTPError

from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from utils.forms import (
    BOOLEAN_WITH_BLANK_CHOICES,
    BootstrapMixin,
    BulkEditForm,
    add_blank_choice,
)
from utils.forms.fields import (
    CommentField,
    ContentTypeChoiceField,
    ContentTypeMultipleChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    SlugField,
    TagFilterField,
    TemplateField,
)
from utils.forms.widgets import (
    APISelectMultiple,
    ColourSelect,
    StaticSelect,
    StaticSelectMultiple,
)

from .enums import HttpMethod, JournalEntryKind
from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JournalEntry,
    Tag,
    Webhook,
)
from .utils import FeatureQuery

__all__ = (
    "ConfigContextAssignmentForm",
    "ConfigContextFilterForm",
    "ConfigContextForm",
    "ExportTemplateFilterForm",
    "ExportTemplateForm",
    "IXAPIFilterForm",
    "IXAPIForm",
    "JournalEntryBulkEditForm",
    "JournalEntryForm",
    "TagBulkEditForm",
    "TagFilterForm",
    "TagForm",
    "WebhookForm",
)


class ConfigContextForm(BootstrapMixin, forms.ModelForm):
    data = JSONField()
    fieldsets = (
        ("Config Context", ("name", "description", "is_active")),
        ("Data", ("data",)),
        ("Data Source", ("data_source", "data_file", "auto_synchronisation_enabled")),
    )

    class Meta:
        model = ConfigContext
        fields = (
            "name",
            "description",
            "is_active",
            "data",
            "data_source",
            "data_file",
            "auto_synchronisation_enabled",
        )

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
        fields = (
            "name",
            "content_type",
            "description",
            "jinja2_trim",
            "jinja2_lstrip",
            "template",
            "data_source",
            "data_file",
            "auto_synchronisation_enabled",
        )
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


class JournalEntryBulkEditForm(BulkEditForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=JournalEntry.objects.all(), widget=forms.MultipleHiddenInput
    )
    kind = forms.ChoiceField(
        choices=add_blank_choice(JournalEntryKind), widget=StaticSelect, required=False
    )
    comments = CommentField()

    model = JournalEntry


class JournalEntryFilterForm(PeeringManagerModelFilterSetForm):
    model = JournalEntry
    created_after = forms.DateTimeField(required=False, label="After")
    created_before = forms.DateTimeField(required=False, label="Before")
    created_by_id = DynamicModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        display_field="username",
        label="User",
        widget=APISelectMultiple(api_url="/api/users/users/"),
    )
    assigned_object_type_id = ContentTypeMultipleChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=FeatureQuery("journaling"),
        required=False,
        label="Object Type",
    )
    kind = forms.ChoiceField(
        choices=add_blank_choice(JournalEntryKind), widget=StaticSelect, required=False
    )
    tag = TagFilterField(model)


class JournalEntryForm(PeeringManagerModelForm):
    kind = forms.ChoiceField(
        choices=add_blank_choice(JournalEntryKind), widget=StaticSelect, required=False
    )
    comments = CommentField()

    class Meta:
        model = JournalEntry
        fields = [
            "assigned_object_type",
            "assigned_object_id",
            "kind",
            "tags",
            "comments",
        ]
        widgets = {
            "assigned_object_type": forms.HiddenInput,
            "assigned_object_id": forms.HiddenInput,
        }


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
        fields = (
            "name",
            "content_types",
            "enabled",
            "type_create",
            "type_update",
            "type_delete",
            "payload_url",
            "http_method",
            "http_content_type",
            "additional_headers",
            "body_template",
            "secret",
            "conditions",
            "ssl_verification",
            "ca_file_path",
        )
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
