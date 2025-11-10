from django import forms

from utils.forms import BOOLEAN_WITH_BLANK_CHOICES, BootstrapMixin
from utils.forms.fields import CommentField, DynamicModelChoiceField
from utils.forms.widgets import DateTimePicker, StaticSelect

from ..models import HiddenPeer, IXLan, Network

__all__ = ("HiddenPeerFilterForm", "HidePeerForm")


class HidePeerForm(BootstrapMixin, forms.ModelForm):
    peeringdb_network = DynamicModelChoiceField(
        queryset=Network.objects.all(), label="Autonomous System"
    )
    peeringdb_ixlan = DynamicModelChoiceField(
        queryset=IXLan.objects.all(), label="Internet Exchange LAN"
    )
    until = forms.DateTimeField(
        required=False, label="Hide until", widget=DateTimePicker()
    )
    comments = CommentField()
    fieldsets = (
        ("Peer to hide", ("peeringdb_network", "peeringdb_ixlan", "until", "comments")),
    )

    class Meta:
        model = HiddenPeer
        fields = ["peeringdb_network", "peeringdb_ixlan", "until", "comments"]


class HiddenPeerFilterForm(BootstrapMixin, forms.Form):
    model = HiddenPeer
    q = forms.CharField(required=False, label="Search")
    peeringdb_network = DynamicModelChoiceField(
        required=False, queryset=Network.objects.all(), label="AS"
    )
    peeringdb_ixlan = DynamicModelChoiceField(
        required=False, queryset=IXLan.objects.all(), label="IXP LAN"
    )
    is_expired = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
        label="Expired",
    )
