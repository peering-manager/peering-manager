from django import forms
from django.contrib.auth.models import User

from utils.forms import BootstrapMixin
from utils.forms.fields import DynamicModelMultipleChoiceField
from utils.forms.widgets import APISelectMultiple, StaticSelectMultiple

from ..enums import JobStatus
from ..models import Job

__all__ = ("JobFilterForm",)


class JobFilterForm(BootstrapMixin, forms.Form):
    model = Job
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False)
    user = DynamicModelMultipleChoiceField(
        required=False,
        queryset=User.objects.all(),
        widget=APISelectMultiple(api_url="/api/users/users/"),
    )
    status = forms.MultipleChoiceField(
        required=False, choices=JobStatus, widget=StaticSelectMultiple
    )
