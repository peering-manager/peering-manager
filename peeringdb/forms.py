from django import forms

from utils.forms import (
    BootstrapMixin,
    BulkEditForm,
    CustomNullBooleanSelect,
    DynamicModelMultipleChoiceField,
    StaticSelectMultiple,
    add_blank_choice,
)

from .enums import GeneralPolicy
from .models import NetworkIXLan


class NetworkIXLanFilterForm(BootstrapMixin, forms.Form):
    model = NetworkIXLan
    q = forms.CharField(required=False, label="Search")
    asn = forms.IntegerField(required=False, label="ASN")
    net__policy_general = forms.ChoiceField(
        label="Peering Policy",
        required=False,
        choices=add_blank_choice(GeneralPolicy.choices),
        widget=StaticSelectMultiple,
    )
    is_rs_peer = forms.NullBooleanField(
        required=False, label="On Route Server", widget=CustomNullBooleanSelect
    )
