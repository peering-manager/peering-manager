from django import forms

from .models import PeerRecord
from utils.forms import BootstrapMixin


class PeerRecordFilterForm(BootstrapMixin, forms.Form):
    model = PeerRecord
    q = forms.CharField(required=False, label="Search")
    network__asn = forms.IntegerField(required=False, label="ASN")
    network__name = forms.CharField(required=False, label="AS Name")
    network__irr_as_set = forms.CharField(required=False, label="IRR AS-SET")
    network__info_prefixes6 = forms.IntegerField(
        required=False, label="IPv6 Max Prefixes"
    )
    network__info_prefixes4 = forms.IntegerField(
        required=False, label="IPv4 Max Prefixes"
    )
