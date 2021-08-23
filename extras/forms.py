from django import forms
from django.contrib.auth.models import User

from utils.forms import (
    APISelectMultiple,
    BootstrapMixin,
    DynamicModelMultipleChoiceField,
    StaticSelect,
    add_blank_choice,
)

from .enums import JobResultStatus
from .models import IXAPI, JobResult


class IXAPIForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = IXAPI
        fields = ("name", "url", "api_key", "api_secret", "identity")


class IXAPIFilterForm(BootstrapMixin, forms.Form):
    model = IXAPI
    q = forms.CharField(required=False, label="Search")


class JobResultFilterForm(BootstrapMixin, forms.Form):
    model = JobResult
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False)
    user_id = DynamicModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        display_field="username",
        label="User",
        widget=APISelectMultiple(api_url="/api/users/users/"),
    )
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(JobResultStatus.choices),
        widget=StaticSelect(),
    )
