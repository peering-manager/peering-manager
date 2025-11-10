from django import forms

from utils.forms import BOOLEAN_WITH_BLANK_CHOICES, BootstrapMixin, add_blank_choice
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from ..enums import (
    ContractsPolicy,
    GeneralPolicy,
    LocationsPolicy,
    NetType,
    Scope,
    Traffic,
)
from ..models import NetworkIXLan

__all__ = ("NetworkIXLanFilterForm",)


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
