from django import forms
from django.contrib.auth.models import User

from utils.forms import BootstrapMixin
from utils.forms.fields import DynamicModelMultipleChoiceField
from utils.forms.widgets import APISelectMultiple, DateTimePicker, StaticSelectMultiple

from ..enums import ObjectChangeAction
from ..models import ObjectChange


class ObjectChangeFilterForm(BootstrapMixin, forms.Form):
    model = ObjectChange
    q = forms.CharField(required=False, label="Search")
    time_after = forms.DateTimeField(
        label="After", required=False, widget=DateTimePicker()
    )
    time_before = forms.DateTimeField(
        label="Before", required=False, widget=DateTimePicker()
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
