from django import forms
from django.contrib.auth.models import User

from utils.forms import BootstrapMixin, add_blank_choice
from utils.forms.fields import DynamicModelMultipleChoiceField
from utils.forms.widgets import APISelectMultiple, StaticSelect

from ..enums import JobStatus
from ..models import Job


class JobFilterForm(BootstrapMixin, forms.Form):
    model = Job
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
        choices=add_blank_choice(JobStatus),
        widget=StaticSelect(),
    )
