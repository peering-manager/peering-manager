from django import forms

from utils.forms import (
    BootstrapMixin,
    BulkEditForm,
    CustomNullBooleanSelect,
    DynamicModelMultipleChoiceField,
)

from .models import NetworkIXLan


class NetworkIXLanFilterForm(BootstrapMixin, forms.Form):
    model = NetworkIXLan
    q = forms.CharField(required=False, label="Search")
    asn = forms.IntegerField(required=False, label="ASN")
