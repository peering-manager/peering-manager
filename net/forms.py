from django import forms
from taggit.forms import TagField

from peering.models import InternetExchange, Router
from utils.fields import CommentField
from utils.forms import (
    BootstrapMixin,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)

from .models import Connection


class ConnectionForm(BootstrapMixin, forms.ModelForm):
    internet_exchange_point = DynamicModelChoiceField(
        required=False,
        queryset=InternetExchange.objects.all(),
        help_text="IXP to which this connection connects",
    )
    router = DynamicModelChoiceField(
        required=False,
        queryset=Router.objects.all(),
        help_text="Router on which this connection is setup",
    )
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Connection
        fields = (
            "vlan",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "router",
            "description",
            "comments",
            "tags",
        )
        labels = {
            "vlan": "VLAN",
            "ipv6_address": "IPv6 address",
            "ipv4_address": "IPv4 address",
        }


class ConnectionFilterForm(BootstrapMixin, forms.Form):
    model = Connection
    q = forms.CharField(required=False, label="Search")
    internet_exchange_point_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=InternetExchange.objects.all(),
        to_field_name="pk",
        label="Internet exchange point",
        null_option="None",
    )
    router_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Router.objects.all(),
        to_field_name="pk",
        null_option="None",
    )
    tag = TagFilterField(model)
