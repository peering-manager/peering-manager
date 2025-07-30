from django import forms

from messaging.models import Email
from peering.models import AutonomousSystem
from utils.forms import BOOLEAN_WITH_BLANK_CHOICES, BootstrapMixin, add_blank_choice
from utils.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TextareaField,
)
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from .enums import (
    ContractsPolicy,
    GeneralPolicy,
    LocationsPolicy,
    NetType,
    Scope,
    Traffic,
)
from .models import Network, NetworkContact, NetworkIXLan

__all__ = ("NetworkIXLanFilterForm", "SendEmailToNetwork")


class NetworkIXLanFilterForm(BootstrapMixin, forms.Form):
    model = NetworkIXLan
    q = forms.CharField(required=False, label="Search")
    asn = forms.IntegerField(required=False, label="ASN")
    is_rs_peer = forms.NullBooleanField(
        required=False,
        label="On Route Server",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    bfd_support = forms.NullBooleanField(
        required=False,
        label="BFD Support",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    net__info_traffic = forms.ChoiceField(
        label="Traffic",
        required=False,
        choices=add_blank_choice(Traffic.choices),
        widget=StaticSelectMultiple,
    )
    net__info_scope = forms.ChoiceField(
        label="Scope",
        required=False,
        choices=add_blank_choice(Scope.choices),
        widget=StaticSelectMultiple,
    )
    net__info_type = forms.ChoiceField(
        label="Type",
        required=False,
        choices=add_blank_choice(NetType.choices),
        widget=StaticSelectMultiple,
    )
    net__policy_general = forms.ChoiceField(
        label="Peering Policy",
        required=False,
        choices=add_blank_choice(GeneralPolicy.choices),
        widget=StaticSelectMultiple,
    )
    net__policy_locations = forms.ChoiceField(
        label="Multiple Locations",
        required=False,
        choices=add_blank_choice(LocationsPolicy.choices),
        widget=StaticSelectMultiple,
    )
    net__policy_ratio = forms.NullBooleanField(
        required=False,
        label="Ratio Requirement",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    net__policy_contracts = forms.ChoiceField(
        label="Contract Requirement",
        required=False,
        choices=add_blank_choice(ContractsPolicy.choices),
        widget=StaticSelectMultiple,
    )


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
