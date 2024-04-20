from django import forms
from django.contrib.auth.models import User

from utils.forms import BootstrapMixin, add_blank_choice
from utils.forms.fields import DynamicModelMultipleChoiceField
from utils.forms.widgets import APISelectMultiple, StaticSelect

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
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(JobStatus),
        widget=StaticSelect(),
    )
