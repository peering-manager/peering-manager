from django import forms
from taggit.forms import TagField

from devices.models import Router
from peering.models import InternetExchange
from peering_manager.forms import (
    PeeringManagerModelBulkEditForm,
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from utils.forms import add_blank_choice
from utils.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    TagFilterField,
)
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from ..enums import ConnectionStatus
from ..models import Connection

__all__ = ("ConnectionBulkEditForm", "ConnectionFilterForm", "ConnectionForm")


class ConnectionForm(PeeringManagerModelForm):
    status = forms.ChoiceField(choices=ConnectionStatus, widget=StaticSelect)
    internet_exchange_point = DynamicModelChoiceField(
        required=False,
        queryset=InternetExchange.objects.all(),
        label="IXP",
        help_text="IXP to which this connection connects",
    )
    router = DynamicModelChoiceField(
        required=False,
        queryset=Router.objects.all(),
        help_text="Router on which this connection is setup",
    )
    comments = CommentField()
    tags = TagField(required=False)
    fieldsets = (
        (
            "Connection",
            (
                "status",
                "vlan",
                "mac_address",
                "ipv6_address",
                "ipv4_address",
                "internet_exchange_point",
                "router",
                "interface",
                "description",
            ),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = Connection
        fields = (
            "status",
            "vlan",
            "mac_address",
            "ipv6_address",
            "ipv4_address",
            "internet_exchange_point",
            "router",
            "interface",
            "description",
            "local_context_data",
            "comments",
            "tags",
        )
        labels = {
            "vlan": "VLAN",
            "ipv6_address": "IPv6 address",
            "ipv4_address": "IPv4 address",
        }


class ConnectionBulkEditForm(PeeringManagerModelBulkEditForm):
    model = Connection
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(ConnectionStatus),
        widget=StaticSelect,
    )
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
    local_context_data = JSONField(required=False)
    nullable_fields = ("router",)


class ConnectionFilterForm(PeeringManagerModelFilterSetForm):
    model = Connection
    status = forms.MultipleChoiceField(
        required=False,
        choices=ConnectionStatus,
        widget=StaticSelectMultiple,
    )
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
        label="Router",
        null_option="None",
    )
    tag = TagFilterField(model)
