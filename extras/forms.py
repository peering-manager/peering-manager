from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from requests.exceptions import HTTPError

from extras.models.configcontext import ConfigContextAssignment
from utils.forms import BootstrapMixin, BulkEditForm
from utils.forms.fields import (
    CommentField,
    ContentTypeChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    SlugField,
)
from utils.forms.widgets import (
    APISelectMultiple,
    ColorSelect,
    CustomNullBooleanSelect,
    StaticSelect,
    StaticSelectMultiple,
)

from .enums import ObjectChangeAction
from .models import IXAPI, ConfigContext, ExportTemplate, ObjectChange, Tag
from .utils import FeatureQuery


class ConfigContextForm(BootstrapMixin, forms.ModelForm):
    data = JSONField()

    class Meta:
        model = ConfigContext
        fields = "__all__"


class ConfigContextFilterForm(BootstrapMixin, forms.Form):
    model = ConfigContext
    q = forms.CharField(required=False, label="Search")
    is_active = forms.NullBooleanField(
        required=False, label="Active", widget=CustomNullBooleanSelect
    )


class ConfigContextAssignmentForm(BootstrapMixin, forms.ModelForm):
    config_context = DynamicModelChoiceField(
        queryset=ConfigContext.objects.filter(is_active=True)
    )

    class Meta:
        model = ConfigContextAssignment
        fields = ("config_context", "weight")


class ExportTemplateForm(BootstrapMixin, forms.ModelForm):
    content_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        limit_choices_to=FeatureQuery("export-templates"),
        label="Object type",
    )

    class Meta:
        model = ExportTemplate
        fields = "__all__"
        widgets = {
            "template": forms.Textarea(attrs={"class": "text-monospace"}),
        }


class ExportTemplateFilterForm(BootstrapMixin, forms.Form):
    model = ExportTemplate
    q = forms.CharField(required=False, label="Search")


class IXAPIForm(BootstrapMixin, forms.ModelForm):
    identity = forms.CharField(widget=StaticSelect)

    class Meta:
        model = IXAPI
        fields = ("name", "url", "api_key", "api_secret", "identity")

    def clean(self):
        cleaned_data = super().clean()

        ixapi = IXAPI(
            url=cleaned_data["url"],
            api_key=cleaned_data["api_key"],
            api_secret=cleaned_data["api_secret"],
        )
        try:
            # Try to query API and see if it raises an error
            ixapi.get_accounts()
        except HTTPError as e:
            # Fail form validation on HTTP error to provide a feedback to the user
            if e.response.status_code >= 400 and e.response.status_code < 500:
                possible_issue = "make sure the URL, key and secret are correct"
            else:
                possible_issue = "the server is malfunctioning or unavailable"
            raise ValidationError(
                f"Unable to connect to IX-API ({e.response.status_code} {e.response.reason}), {possible_issue}."
            )


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


class TagBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), widget=forms.MultipleHiddenInput
    )
    color = forms.CharField(max_length=6, required=False, widget=ColorSelect())

    class Meta:
        nullable_fields = ["comments"]


class TagFilterForm(BootstrapMixin, forms.Form):
    model = Tag
    q = forms.CharField(required=False, label="Search")


class TagForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()
    comments = CommentField()

    class Meta:
        model = Tag
        fields = ["name", "slug", "color", "comments"]
