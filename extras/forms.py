from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from requests.exceptions import HTTPError

from extras.models.configcontext import ConfigContextAssignment
from utils.forms import BootstrapMixin
from utils.forms.fields import (
    ContentTypeChoiceField,
    DynamicModelChoiceField,
    JSONField,
)
from utils.forms.widgets import CustomNullBooleanSelect, StaticSelect

from .models import IXAPI, ConfigContext, ExportTemplate
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
