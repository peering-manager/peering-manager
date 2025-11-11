from django import forms

from messaging.models import Email
from peering.models import AutonomousSystem
from utils.forms import BootstrapMixin
from utils.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TextareaField,
)
from utils.forms.widgets import StaticSelectMultiple

from ..models import Network, NetworkContact

__all__ = ("SendEmailToNetwork",)


class SendEmailToNetwork(BootstrapMixin, forms.Form):
    affiliated = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    network = DynamicModelChoiceField(
        queryset=Network.objects.all(), label="Autonomous system"
    )
    email = DynamicModelChoiceField(
        required=False, queryset=Email.objects.all(), label="Template"
    )
    recipients = DynamicModelMultipleChoiceField(
        queryset=NetworkContact.objects.exclude(email=""),
        query_params={"net_id": "$network"},
    )
    cc = forms.MultipleChoiceField(
        widget=StaticSelectMultiple, label="Carbon copy", required=False
    )
    subject = forms.CharField(label="Subject")
    body = TextareaField(label="Body", required=True)
