from django import forms
from taggit.forms import TagField

from peering.models import InternetExchange, Router
from utils.forms import (
    AddRemoveTagsForm,
    BootstrapMixin,
    BulkEditForm,
    TagFilterField,
    add_blank_choice,
)
from utils.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
)
from utils.forms.widgets import SmallTextarea, StaticSelect

from .enums import ConnectionState
from .models import Connection


class ConnectionForm(BootstrapMixin, forms.ModelForm):
    state = forms.ChoiceField(choices=ConnectionState.choices, widget=StaticSelect)
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
    local_context_data = JSONField(
        required=False, label="Local context data", widget=SmallTextarea
    )
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Connection
        fields = (
            "state",
            "vlan",
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


class ConnectionBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=Connection.objects.all(), widget=forms.MultipleHiddenInput
    )
    state = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(ConnectionState.choices),
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
    local_context_data = JSONField(
        required=False, label="Local context data", widget=SmallTextarea
    )

    class Meta:
        model = Connection
        fields = ("state", "internet_exchange_point", "router", "local_context_data")
        nullable_fields = ("router",)


class ConnectionFilterForm(BootstrapMixin, forms.Form):
    model = Connection
    q = forms.CharField(required=False, label="Search")
    state = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(ConnectionState.choices),
        widget=StaticSelect,
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
