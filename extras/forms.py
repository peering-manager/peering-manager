from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from requests.exceptions import HTTPError

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
            ixapi.get_customers()
        except HTTPError as e:
            # Fail form validation on HTTP error to provide a feedback to the user
            message = f"Unable to connect to IX-API ({e.response.status_code} {e.response.reason})"
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
