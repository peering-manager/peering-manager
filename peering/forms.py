from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from taggit.forms import TagField

from bgp.models import Community, Relationship
from devices.enums import DeviceStatus
from devices.models import Router
from extras.models import IXAPI
from messaging.models import Email
from net.models import BFD, Connection
from peering_manager.forms import (
    PeeringManagerModelBulkEditForm,
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from utils.forms import BOOLEAN_WITH_BLANK_CHOICES, BootstrapMixin, add_blank_choice
from utils.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    PasswordField,
    SlugField,
    TagFilterField,
    TextareaField,
)
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from .enums import (
    BGPGroupStatus,
    BGPSessionStatus,
    BGPState,
    IPFamily,
    RoutingPolicyType,
)
from .models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)

if TYPE_CHECKING:
    from ipaddress import IPv4Interface, IPv6Interface


class AutonomousSystemForm(PeeringManagerModelForm):
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_context_data = JSONField(required=False)
    comments = CommentField()
    tags = TagField(required=False)

    fieldsets = (
        (
            "Autonomous System",
            (
                "asn",
                "name",
                "description",
                "affiliated",
                "irr_as_set",
                "ipv6_max_prefixes",
                "ipv4_max_prefixes",
            ),
        ),
        (
            "Routing Policies",
            ("import_routing_policies", "export_routing_policies", "communities"),
        ),
        (
            "Synchronise with PeeringDB (if public AS)",
            (
                "name_peeringdb_sync",
                "irr_as_set_peeringdb_sync",
                "ipv6_max_prefixes_peeringdb_sync",
                "ipv4_max_prefixes_peeringdb_sync",
            ),
        ),
        (
            "IRR Objects Retrieval",
            (
                "retrieve_prefixes",
                "retrieve_as_list",
                "irr_sources_override",
                "irr_ipv6_prefixes_args_override",
                "irr_ipv4_prefixes_args_override",
            ),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = AutonomousSystem
        fields = (
            "asn",
            "name",
            "name_peeringdb_sync",
            "description",
            "irr_as_set",
            "irr_as_set_peeringdb_sync",
            "ipv6_max_prefixes",
            "ipv6_max_prefixes_peeringdb_sync",
            "ipv4_max_prefixes",
            "ipv4_max_prefixes_peeringdb_sync",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "local_context_data",
            "comments",
            "retrieve_prefixes",
            "retrieve_as_list",
            "irr_sources_override",
            "irr_ipv6_prefixes_args_override",
            "irr_ipv4_prefixes_args_override",
            "affiliated",
            "tags",
        )
        labels = {
            "name_peeringdb_sync": "Name",
            "irr_as_set_peeringdb_sync": "IRR AS-SET",
            "ipv6_max_prefixes_peeringdb_sync": "IPv6 max prefixes",
            "ipv4_max_prefixes_peeringdb_sync": "IPv4 max prefixes",
            "irr_sources_override": "IRR sources override",
            "irr_ipv6_prefixes_args_override": "IRR IPv6 prefixes override",
            "irr_ipv4_prefixes_args_override": "IRR IPv4 prefixes override",
        }
        help_texts = {
            "asn": "BGP autonomous system number (32-bit capable)",
            "name": "Full name of the AS",
            "affiliated": "Check if you own/manage this AS",
            "retrieve_prefixes": "Retrieve and cache prefixes from IRR sources",
            "retrieve_as_list": "Retrieve and cache AS list from IRR sources",
            "irr_sources_override": (
                "Override the IRR sources to use for this AS; if empty, "
                f"<code>{settings.BGPQ3_SOURCES}</code> will be used"
            ),
            "irr_ipv6_prefixes_args_override": (
                "Override the arguments to pass to bgpq3/bgpq4 for IPv6 prefixes; "
                f"if empty, <code>{' '.join(settings.BGPQ3_ARGS['ipv6'])}</code> "
                "will be used"
            ),
            "irr_ipv4_prefixes_args_override": (
                "Override the arguments to pass to bgpq3/bgpq4 for IPv4 prefixes; "
                f"if empty, <code>{' '.join(settings.BGPQ3_ARGS['ipv4'])}</code> "
                "will be used"
            ),
        }


class AutonomousSystemFilterForm(PeeringManagerModelFilterSetForm):
    model = AutonomousSystem
    asn = forms.IntegerField(required=False, label="ASN")
    ipv6_max_prefixes = forms.IntegerField(required=False, label="IPv6 max prefixes")
    ipv4_max_prefixes = forms.IntegerField(required=False, label="IPv4 max prefixes")
    affiliated = forms.NullBooleanField(
        required=False,
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    tag = TagFilterField(model)


class AutonomousSystemEmailForm(BootstrapMixin, forms.Form):
    email = DynamicModelChoiceField(
        required=False, queryset=Email.objects.all(), label="Template"
    )
    recipient = forms.MultipleChoiceField(
        widget=StaticSelectMultiple, label="Recipients"
    )
    cc = forms.MultipleChoiceField(
        widget=StaticSelectMultiple, label="Carbon copy", required=False
    )
    subject = forms.CharField(label="Subject")
    body = TextareaField(label="Body")


class BGPGroupForm(PeeringManagerModelForm):
    slug = SlugField(
        max_length=255,
        help_text="Friendly unique shorthand used for URL and config. Warning: may result in change of operational state on a router if being used in the configuration.",
    )
    status = forms.ChoiceField(
        required=False, choices=DeviceStatus, widget=StaticSelect
    )
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_context_data = JSONField(required=False)
    tags = TagField(required=False)
    fieldsets = (
        (
            "BGP Group",
            ("name", "slug", "description", "status"),
        ),
        (
            "Routing Policies",
            (
                "import_routing_policies",
                "export_routing_policies",
                "communities",
            ),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = BGPGroup
        fields = (
            "name",
            "slug",
            "description",
            "status",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "local_context_data",
            "tags",
        )
        help_texts = {"name": "Full name of the BGP group"}


class BGPGroupBulkEditForm(PeeringManagerModelBulkEditForm):
    status = forms.ChoiceField(
        required=False, choices=add_blank_choice(DeviceStatus), widget=StaticSelect
    )
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )

    model = BGPGroup
    nullable_fields = (
        "description",
        "import_routing_policies",
        "export_routing_policies",
        "communities",
    )


class BGPGroupFilterForm(PeeringManagerModelFilterSetForm):
    model = BGPGroup
    status = forms.MultipleChoiceField(
        required=False, choices=BGPGroupStatus, widget=StaticSelectMultiple
    )
    tag = TagFilterField(model)


class DirectPeeringSessionForm(PeeringManagerModelForm):
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    autonomous_system = DynamicModelChoiceField(queryset=AutonomousSystem.objects.all())
    bgp_group = DynamicModelChoiceField(
        required=False, queryset=BGPGroup.objects.all(), label="BGP Group"
    )
    status = forms.ChoiceField(
        required=False,
        choices=BGPSessionStatus,
        initial=BGPSessionStatus.ENABLED,
        widget=StaticSelect,
    )
    relationship = DynamicModelChoiceField(queryset=Relationship.objects.all())
    router = DynamicModelChoiceField(
        required=False,
        queryset=Router.objects.all(),
        help_text="Router on which this session is configured",
    )
    connection = DynamicModelChoiceField(
        required=False,
        queryset=Connection.objects.all(),
        help_text="Network connection on which this session lives",
    )
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    bfd = DynamicModelChoiceField(
        required=False,
        queryset=BFD.objects.all(),
        label="BFD",
        help_text="BFD configuration to use for liveness detection",
    )
    password = PasswordField(required=False, render_value=True)
    local_context_data = JSONField(required=False)
    comments = CommentField()
    tags = TagField(required=False)
    fieldsets = (
        ("Peer", ("bgp_group", "relationship", "autonomous_system", "ip_address")),
        (
            "Local",
            ("local_autonomous_system", "local_ip_address", "router", "connection"),
        ),
        (
            "Properties",
            (
                "service_reference",
                "status",
                "password",
                "multihop_ttl",
                "passive",
                "bfd",
            ),
        ),
        (
            "Routing Policies",
            ("import_routing_policies", "export_routing_policies", "communities"),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = DirectPeeringSession
        fields = (
            "service_reference",
            "local_autonomous_system",
            "local_ip_address",
            "autonomous_system",
            "bgp_group",
            "status",
            "relationship",
            "ip_address",
            "password",
            "multihop_ttl",
            "passive",
            "router",
            "connection",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "bfd",
            "local_context_data",
            "comments",
            "tags",
        )
        labels = {"local_ip_address": "Local IP Address", "ip_address": "IP Address"}
        help_texts = {
            "local_ip_address": "IPv6 or IPv4 address",
            "ip_address": "IPv6 or IPv4 address",
            "passive": "Wait for the peer to issue an open request before a message is sent",
        }

    def clean(self):
        cleaned_data = super().clean()

        # Invalid IP address, let the field validator handle it
        if "ip_address" not in cleaned_data:
            return

        ip_dst: IPv6Interface | IPv4Interface = cleaned_data["ip_address"]

        # Make sure that routing policies are compatible (address family)
        for policy in cleaned_data["import_routing_policies"].union(
            cleaned_data["export_routing_policies"]
        ):
            if policy.address_family not in (IPFamily.ALL, ip_dst.version):
                raise ValidationError(
                    f"Routing policy '{policy.name}' cannot be used for this session, address families mismatch."
                )


class DirectPeeringSessionBulkEditForm(PeeringManagerModelBulkEditForm):
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(BGPSessionStatus),
        widget=StaticSelect,
    )
    relationship = DynamicModelChoiceField(
        required=False, queryset=Relationship.objects.all()
    )
    bgp_group = DynamicModelChoiceField(
        required=False, queryset=BGPGroup.objects.all(), label="BGP group"
    )
    passive = forms.NullBooleanField(
        required=False, widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    bfd = DynamicModelChoiceField(
        required=False, queryset=BFD.objects.all(), label="BFD"
    )
    router = DynamicModelChoiceField(required=False, queryset=Router.objects.all())
    local_context_data = JSONField(required=False)
    comments = CommentField()

    model = DirectPeeringSession
    nullable_fields = (
        "import_routing_policies",
        "export_routing_policies",
        "communities",
        "bfd",
        "router",
        "connection",
        "local_context_data",
        "comments",
    )


class DirectPeeringSessionFilterForm(PeeringManagerModelFilterSetForm):
    model = DirectPeeringSession
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        to_field_name="pk",
        label="Local AS",
    )
    autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        to_field_name="pk",
        label="Autonomous system",
    )
    bgp_group_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=BGPGroup.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="BGP group",
    )
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily, widget=StaticSelect
    )
    status = forms.MultipleChoiceField(
        required=False, choices=BGPSessionStatus, widget=StaticSelectMultiple
    )
    relationship_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Relationship.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Relationship",
    )
    bfd_id = DynamicModelMultipleChoiceField(
        required=False, queryset=BFD.objects.all(), to_field_name="pk", label="BFD"
    )
    router_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Router.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Router",
    )
    connection_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Connection.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Connection",
    )
    passive = forms.NullBooleanField(
        required=False, widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )
    bgp_state = forms.MultipleChoiceField(
        required=False, choices=BGPState, widget=StaticSelectMultiple, label="BGP state"
    )
    tag = TagFilterField(model)


class InternetExchangeForm(PeeringManagerModelForm):
    slug = SlugField(
        max_length=255,
        help_text="Friendly unique shorthand used for URL and config. Warning: may result in change of operational state on a router if being used in the configuration.",
    )
    status = forms.ChoiceField(
        required=False, choices=DeviceStatus, widget=StaticSelect
    )
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_context_data = JSONField(required=False)
    ixapi_endpoint = DynamicModelChoiceField(
        required=False, label="IX-API endpoint", queryset=IXAPI.objects.all()
    )
    tags = TagField(required=False)
    fieldsets = (
        (
            "Internet Exchange Point",
            ("name", "slug", "description", "status", "local_autonomous_system"),
        ),
        (
            "Routing Policies",
            ("import_routing_policies", "export_routing_policies", "communities"),
        ),
        ("Config Context", ("local_context_data",)),
        ("Third Party", ("ixapi_endpoint",)),
    )

    class Meta:
        model = InternetExchange
        fields = (
            "name",
            "slug",
            "description",
            "status",
            "local_autonomous_system",
            "communities",
            "import_routing_policies",
            "export_routing_policies",
            "local_context_data",
            "ixapi_endpoint",
            "tags",
        )
        help_texts = {"name": "Full name of the Internet Exchange point"}


class InternetExchangeBulkEditForm(PeeringManagerModelBulkEditForm):
    status = forms.ChoiceField(
        required=False, choices=add_blank_choice(DeviceStatus), widget=StaticSelect
    )
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_context_data = JSONField(required=False)
    ixapi_endpoint = DynamicModelChoiceField(
        required=False, label="IX-API endpoint", queryset=IXAPI.objects.all()
    )

    model = InternetExchange
    nullable_fields = (
        "description",
        "import_routing_policies",
        "export_routing_policies",
        "communities",
        "local_context_data",
        "ixapi_endpoint",
    )


class InternetExchangePeeringDBForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.fields["peeringdb_ixlan"].widget = forms.HiddenInput()

    class Meta:
        model = InternetExchange
        fields = ("peeringdb_ixlan", "local_autonomous_system", "name", "slug")
        help_texts = {"name": "Full name of the Internet Exchange point"}


class InternetExchangeFilterForm(PeeringManagerModelFilterSetForm):
    model = InternetExchange
    status = forms.MultipleChoiceField(
        required=False, choices=BGPGroupStatus, widget=StaticSelectMultiple
    )
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local AS",
    )
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        to_field_name="pk",
        null_option="None",
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        to_field_name="pk",
        null_option="None",
        query_params={"type": "export-policy"},
    )
    tag = TagFilterField(model)


class InternetExchangePeeringSessionBulkEditForm(PeeringManagerModelBulkEditForm):
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(BGPSessionStatus),
        widget=StaticSelect,
    )
    is_route_server = forms.NullBooleanField(
        required=False,
        label="Route server",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    passive = forms.NullBooleanField(
        required=False, widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    bfd = DynamicModelChoiceField(
        required=False, queryset=BFD.objects.all(), label="BFD"
    )
    local_context_data = JSONField(required=False)
    comments = CommentField()

    model = InternetExchangePeeringSession
    nullable_fields = (
        "import_routing_policies",
        "export_routing_policies",
        "communities",
        "bfd",
        "local_context_data",
        "comments",
    )


class InternetExchangePeeringSessionForm(PeeringManagerModelForm):
    autonomous_system = DynamicModelChoiceField(queryset=AutonomousSystem.objects.all())
    internet_exchange = DynamicModelChoiceField(
        required=False, queryset=InternetExchange.objects.all(), label="IXP"
    )
    ixp_connection = DynamicModelChoiceField(
        queryset=Connection.objects.all(),
        query_params={"internet_exchange_point_id": "$internet_exchange"},
        label="IXP connection",
    )
    status = forms.ChoiceField(
        required=False,
        choices=BGPSessionStatus,
        initial=BGPSessionStatus.ENABLED,
        widget=StaticSelect,
    )
    password = PasswordField(required=False, render_value=True)
    import_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "import-policy"},
    )
    export_routing_policies = DynamicModelMultipleChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        query_params={"type": "export-policy"},
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    bfd = DynamicModelChoiceField(
        required=False,
        queryset=BFD.objects.all(),
        label="BFD",
        help_text="BFD configuration to use for liveness detection",
    )
    local_context_data = JSONField(required=False)
    comments = CommentField()
    tags = TagField(required=False)
    fieldsets = (
        ("Internet Exchange Point", ("internet_exchange", "ixp_connection")),
        ("Peer", ("autonomous_system", "ip_address", "is_route_server")),
        (
            "Properties",
            (
                "service_reference",
                "status",
                "password",
                "multihop_ttl",
                "passive",
                "bfd",
            ),
        ),
        (
            "Routing Policies",
            ("import_routing_policies", "export_routing_policies", "communities"),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = InternetExchangePeeringSession
        fields = (
            "service_reference",
            "autonomous_system",
            "ixp_connection",
            "status",
            "ip_address",
            "password",
            "multihop_ttl",
            "passive",
            "is_route_server",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "bfd",
            "local_context_data",
            "comments",
            "tags",
        )
        help_texts = {
            "ip_address": "IPv6 or IPv4 address",
            "passive": "Wait for the peer to issue an open request before a message is sent",
            "is_route_server": "Define if this session is with a route server",
        }

    def clean(self):
        cleaned_data = super().clean()

        # Make sure that routing policies are compatible (address family)
        for policy in (
            cleaned_data["import_routing_policies"]
            | cleaned_data["export_routing_policies"]
        ):
            if policy.address_family not in (
                IPFamily.ALL,
                cleaned_data["ip_address"].version,
            ):
                raise ValidationError(
                    f"Routing policy '{policy.name}' cannot be used for this session, address families mismatch."
                )


class InternetExchangePeeringSessionFilterForm(PeeringManagerModelFilterSetForm):
    model = InternetExchangePeeringSession
    autonomous_system_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        to_field_name="pk",
        label="Autonomous system",
    )
    ixp_connection_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Connection.objects.all(),
        to_field_name="pk",
        label="IXP connection",
    )
    bfd_id = DynamicModelMultipleChoiceField(
        required=False, queryset=BFD.objects.all(), to_field_name="pk", label="BFD"
    )
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily, widget=StaticSelect
    )
    status = forms.MultipleChoiceField(
        required=False, choices=BGPSessionStatus, widget=StaticSelectMultiple
    )
    passive = forms.NullBooleanField(
        required=False, widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )
    is_route_server = forms.NullBooleanField(
        required=False,
        label="Route server",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    exists_in_peeringdb = forms.NullBooleanField(
        required=False,
        label="In PeeringDB",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    is_abandoned = forms.NullBooleanField(
        required=False,
        label="Is Abandoned",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    bgp_state = forms.MultipleChoiceField(
        required=False, choices=BGPState, widget=StaticSelectMultiple, label="BGP state"
    )
    tag = TagFilterField(model)


class RoutingPolicyForm(PeeringManagerModelForm):
    slug = SlugField(max_length=255)
    type = forms.ChoiceField(choices=RoutingPolicyType, widget=StaticSelect)
    address_family = forms.ChoiceField(choices=IPFamily, widget=StaticSelect)
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_context_data = JSONField(required=False)
    tags = TagField(required=False)
    fieldsets = (
        (
            "Routing Policy",
            (
                "name",
                "slug",
                "description",
                "type",
                "weight",
                "address_family",
                "communities",
            ),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = RoutingPolicy

        fields = (
            "name",
            "slug",
            "description",
            "type",
            "weight",
            "address_family",
            "communities",
            "local_context_data",
            "tags",
        )


class RoutingPolicyBulkEditForm(PeeringManagerModelBulkEditForm):
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(RoutingPolicyType),
        widget=StaticSelect,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily, widget=StaticSelect
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_context_data = JSONField(required=False)

    model = RoutingPolicy
    nullable_fields = ("description", "communities", "local_context_data")


class RoutingPolicyFilterForm(PeeringManagerModelFilterSetForm):
    model = RoutingPolicy
    type = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(RoutingPolicyType),
        widget=StaticSelectMultiple,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=add_blank_choice(IPFamily), widget=StaticSelect
    )
    tag = TagFilterField(model)
