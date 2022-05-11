from django import forms

from utils.forms import BootstrapMixin, add_blank_choice
from utils.forms.widgets import CustomNullBooleanSelect, StaticSelectMultiple

from .enums import (
    ContractsPolicy,
    GeneralPolicy,
    LocationsPolicy,
    NetType,
    Scope,
    Traffic,
)
from .models import NetworkIXLan


class NetworkIXLanFilterForm(BootstrapMixin, forms.Form):
    model = NetworkIXLan
    q = forms.CharField(required=False, label="Search")
    asn = forms.IntegerField(required=False, label="ASN")
    is_rs_peer = forms.NullBooleanField(
        required=False, label="On Route Server", widget=CustomNullBooleanSelect
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
        required=False, label="Ratio Requirement", widget=CustomNullBooleanSelect
    )
    net__policy_contracts = forms.ChoiceField(
        label="Contract Requirement",
        required=False,
        choices=add_blank_choice(ContractsPolicy.choices),
        widget=StaticSelectMultiple,
    )
