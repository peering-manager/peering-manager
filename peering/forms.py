from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from taggit.forms import TagField

from bgp.models import Relationship
from devices.models import Configuration, Platform
from extras.models.ix_api import IXAPI
from messaging.models import Email
from net.models import Connection
from netbox.api import NetBox
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
    PasswordField,
    SlugField,
    TextareaField,
)
from utils.forms.widgets import (
    CustomNullBooleanSelect,
    SmallTextarea,
    StaticSelect,
    StaticSelectMultiple,
)

from .enums import (
    BGPGroupStatus,
    BGPSessionStatus,
    CommunityType,
    DeviceStatus,
    IPFamily,
    RoutingPolicyType,
)
from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)


class AutonomousSystemForm(BootstrapMixin, forms.ModelForm):
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
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = AutonomousSystem
        fields = (
            "asn",
            "name",
            "name_peeringdb_sync",
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
            "affiliated",
            "tags",
        )
        labels = {
            "name_peeringdb_sync": "Name",
            "irr_as_set_peeringdb_sync": "IRR AS-SET",
            "ipv6_max_prefixes_peeringdb_sync": "IPv6 max prefixes",
            "ipv4_max_prefixes_peeringdb_sync": "IPv4 max prefixes",
        }
        help_texts = {
            "asn": "BGP autonomous system number (32-bit capable)",
            "name": "Full name of the AS",
            "affiliated": "Check if you own/manage this AS",
        }


class AutonomousSystemFilterForm(BootstrapMixin, forms.Form):
    model = AutonomousSystem
    q = forms.CharField(required=False, label="Search")
    asn = forms.IntegerField(required=False, label="ASN")
    ipv6_max_prefixes = forms.IntegerField(required=False, label="IPv6 max prefixes")
    ipv4_max_prefixes = forms.IntegerField(required=False, label="IPv4 max prefixes")
    affiliated = forms.NullBooleanField(required=False, widget=CustomNullBooleanSelect)
    tag = TagFilterField(model)


class AutonomousSystemEmailForm(BootstrapMixin, forms.Form):
    email = DynamicModelChoiceField(required=False, queryset=Email.objects.all())
    recipient = forms.MultipleChoiceField(
        widget=StaticSelectMultiple, label="E-mail recipient"
    )
    cc = forms.MultipleChoiceField(
        widget=StaticSelectMultiple, label="E-mail CC", required=False
    )
    subject = forms.CharField(label="E-mail subject")
    body = TextareaField(label="E-mail body")


class BGPGroupForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(
        max_length=255,
        help_text="Friendly unique shorthand used for URL and config. Warning: may result in change of operational state on a router if being used in the configuration.",
    )
    status = forms.ChoiceField(
        required=False, choices=DeviceStatus, widget=StaticSelect
    )
    comments = CommentField()
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
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    tags = TagField(required=False)

    class Meta:
        model = BGPGroup
        fields = (
            "name",
            "slug",
            "status",
            "comments",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "local_context_data",
            "tags",
        )
        help_texts = {"name": "Full name of the BGP group"}


class BGPGroupBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=BGPGroup.objects.all(), widget=forms.MultipleHiddenInput
    )
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
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = (
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "comments",
        )


class BGPGroupFilterForm(BootstrapMixin, forms.Form):
    model = BGPGroup
    q = forms.CharField(required=False, label="Search")
    status = forms.MultipleChoiceField(
        required=False, choices=BGPGroupStatus, widget=StaticSelectMultiple
    )
    tag = TagFilterField(model)


class CommunityForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType),
        widget=StaticSelect,
        help_text="Optional, Ingress for received routes, Egress for advertised routes",
    )
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Community

        fields = (
            "name",
            "value",
            "slug",
            "type",
            "local_context_data",
            "comments",
            "tags",
        )
        help_texts = {
            "value": 'Community (<a target="_blank" href="https://tools.ietf.org/html/rfc1997">RFC1997</a>), Extended Community (<a target="_blank" href="https://tools.ietf.org/html/rfc4360">RFC4360</a>) or Large Community (<a target="_blank" href="https://tools.ietf.org/html/rfc8092">RFC8092</a>)'
        }


class CommunityBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=Community.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType),
        widget=StaticSelect,
    )
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ("type", "local_context_data", "comments")


class CommunityFilterForm(BootstrapMixin, forms.Form):
    model = Community
    q = forms.CharField(required=False, label="Search")
    type = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType),
        widget=StaticSelectMultiple,
    )
    tag = TagFilterField(model)


class DirectPeeringSessionForm(BootstrapMixin, forms.ModelForm):
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
        label="Local AS",
    )
    autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes")
    )
    bgp_group = DynamicModelChoiceField(
        required=False, queryset=BGPGroup.objects.all(), label="BGP Group"
    )
    status = forms.ChoiceField(
        required=False, choices=BGPSessionStatus, widget=StaticSelect
    )
    relationship = DynamicModelChoiceField(queryset=Relationship.objects.all())
    router = DynamicModelChoiceField(
        required=False,
        queryset=Router.objects.all(),
        help_text="Router on which this session is configured",
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
    password = PasswordField(required=False, render_value=True)
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField()
    tags = TagField(required=False)

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
            "router",
            "import_routing_policies",
            "export_routing_policies",
            "local_context_data",
            "comments",
            "tags",
        )
        labels = {
            "local_ip_address": "Local IP Address",
            "ip_address": "IP Address",
        }
        help_texts = {
            "local_ip_address": "IPv6 or IPv4 address",
            "ip_address": "IPv6 or IPv4 address",
        }

    def clean(self):
        cleaned_data = super().clean()

        ip_src = cleaned_data["local_ip_address"]
        ip_dst = cleaned_data["ip_address"]

        # Make sure that both local qnd remote IP addresses belong in the same subnet
        if (
            cleaned_data["multihop_ttl"] == 1
            and ip_src
            and (ip_src.network != ip_dst.network)
        ):
            raise ValidationError(
                f"{ip_src} and {ip_dst} don't belong to the same subnet."
            )

        # Make sure that routing policies are compatible (address family)
        for policy in cleaned_data["import_routing_policies"].union(
            cleaned_data["export_routing_policies"]
        ):
            if (
                policy.address_family != IPFamily.ALL
                and policy.address_family != ip_dst.version
            ):
                raise ValidationError(
                    f"Routing policy '{policy.name}' cannot be used for this session, address families mismatch."
                )


class DirectPeeringSessionBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=DirectPeeringSession.objects.all(), widget=forms.MultipleHiddenInput
    )
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
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
    router = DynamicModelChoiceField(required=False, queryset=Router.objects.all())
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField()

    class Meta:
        nullable_fields = (
            "import_routing_policies",
            "export_routing_policies",
            "router",
            "local_context_data",
            "comments",
        )


class DirectPeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = DirectPeeringSession
    q = forms.CharField(required=False, label="Search")
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
        to_field_name="pk",
        label="Local AS",
    )
    autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
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
    router_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Router.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Router",
    )
    tag = TagFilterField(model)


class InternetExchangeForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(
        max_length=255,
        help_text="Friendly unique shorthand used for URL and config. Warning: may result in change of operational state on a router if being used in the configuration.",
    )
    status = forms.ChoiceField(
        required=False, choices=DeviceStatus, widget=StaticSelect
    )
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes"),
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
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    ixapi_endpoint = DynamicModelChoiceField(
        required=False, label="IX-API endpoint", queryset=IXAPI.objects.all()
    )
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = InternetExchange
        fields = (
            "name",
            "slug",
            "status",
            "local_autonomous_system",
            "communities",
            "import_routing_policies",
            "export_routing_policies",
            "local_context_data",
            "ixapi_endpoint",
            "comments",
            "tags",
        )
        help_texts = {"name": "Full name of the Internet Exchange point"}


class InternetExchangeBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=InternetExchange.objects.all(), widget=forms.MultipleHiddenInput
    )
    status = forms.ChoiceField(
        required=False, choices=add_blank_choice(DeviceStatus), widget=StaticSelect
    )
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
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
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    ixapi_endpoint = DynamicModelChoiceField(
        required=False, label="IX-API endpoint", queryset=IXAPI.objects.all()
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = (
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "local_context_data",
            "ixapi_endpoint",
            "comments",
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


class InternetExchangeFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchange
    q = forms.CharField(required=False, label="Search")
    status = forms.MultipleChoiceField(
        required=False, choices=BGPGroupStatus, widget=StaticSelectMultiple
    )
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
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


class InternetExchangePeeringSessionBulkEditForm(
    BootstrapMixin, AddRemoveTagsForm, BulkEditForm
):
    pk = DynamicModelMultipleChoiceField(
        queryset=InternetExchangePeeringSession.objects.all(),
        widget=forms.MultipleHiddenInput,
    )
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(BGPSessionStatus),
        widget=StaticSelect,
    )
    is_route_server = forms.NullBooleanField(
        required=False, label="Route server", widget=CustomNullBooleanSelect
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
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = (
            "import_routing_policies",
            "export_routing_policies",
            "local_context_data",
            "comments",
        )


class InternetExchangePeeringSessionForm(BootstrapMixin, forms.ModelForm):
    autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes")
    )
    internet_exchange = DynamicModelChoiceField(
        required=False, queryset=InternetExchange.objects.all(), label="IXP"
    )
    ixp_connection = DynamicModelChoiceField(
        queryset=Connection.objects.all(),
        query_params={"internet_exchange_point_id": "$internet_exchange"},
        label="IXP connection",
    )
    status = forms.ChoiceField(
        required=False, choices=BGPSessionStatus, widget=StaticSelect
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
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField()
    tags = TagField(required=False)

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
            "is_route_server",
            "import_routing_policies",
            "export_routing_policies",
            "local_context_data",
            "comments",
            "tags",
        )
        help_texts = {
            "ip_address": "IPv6 or IPv4 address",
            "is_route_server": "Define if this session is with a route server",
        }

    def clean(self):
        cleaned_data = super().clean()

        # Make sure that routing policies are compatible (address family)
        for policy in (
            cleaned_data["import_routing_policies"]
            | cleaned_data["export_routing_policies"]
        ):
            if (
                policy.address_family != IPFamily.ALL
                and policy.address_family != cleaned_data["ip_address"].version
            ):
                raise ValidationError(
                    f"Routing policy '{policy.name}' cannot be used for this session, address families mismatch."
                )


class InternetExchangePeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    autonomous_system_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
        to_field_name="pk",
        label="Autonomous system",
    )
    ixp_connection_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Connection.objects.all(),
        to_field_name="pk",
        label="IXP connection",
    )
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily, widget=StaticSelect
    )
    status = forms.MultipleChoiceField(
        required=False, choices=BGPSessionStatus, widget=StaticSelectMultiple
    )
    is_route_server = forms.NullBooleanField(
        required=False, label="Route server", widget=CustomNullBooleanSelect
    )
    tag = TagFilterField(model)


class RouterForm(BootstrapMixin, forms.ModelForm):
    netbox_device_id = forms.IntegerField(label="NetBox device", initial=0)
    platform = DynamicModelChoiceField(required=False, queryset=Platform.objects.all())
    status = forms.ChoiceField(
        required=False, choices=DeviceStatus, widget=StaticSelect
    )
    configuration_template = DynamicModelChoiceField(
        required=False,
        queryset=Configuration.objects.all(),
        label="Configuration",
        help_text="Template used to generate device configuration",
    )
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
        label="Local AS",
    )
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    napalm_username = forms.CharField(required=False, label="Username")
    napalm_password = PasswordField(required=False, render_value=True, label="Password")
    napalm_timeout = forms.IntegerField(
        required=False,
        label="Timeout",
        help_text="The maximum time to wait for a connection in seconds",
    )
    napalm_args = JSONField(
        required=False,
        label="Optional arguments",
        help_text="See NAPALM's <a href='http://napalm.readthedocs.io/en/latest/support/#optional-arguments'>documentation</a> for a complete list of optional arguments",
        widget=SmallTextarea,
    )
    comments = CommentField()
    tags = TagField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings.NETBOX_API:
            choices = []
            for device in NetBox().get_devices():
                try:
                    choices.append((device.id, device.display))
                except AttributeError:
                    # Fallback to hold API attribute
                    choices.append((device.id, device.display_name))

            self.fields["netbox_device_id"] = forms.ChoiceField(
                label="NetBox device",
                choices=[(0, "---------")] + choices,
                widget=StaticSelect,
            )
            self.fields["netbox_device_id"].widget.attrs["class"] = " ".join(
                [
                    self.fields["netbox_device_id"].widget.attrs.get("class", ""),
                    "form-control",
                ]
            ).strip()
        else:
            self.fields["netbox_device_id"].widget = forms.HiddenInput()

    class Meta:
        model = Router

        fields = (
            "netbox_device_id",
            "use_netbox",
            "name",
            "hostname",
            "platform",
            "status",
            "encrypt_passwords",
            "poll_bgp_sessions_state",
            "configuration_template",
            "local_autonomous_system",
            "local_context_data",
            "napalm_username",
            "napalm_password",
            "napalm_timeout",
            "napalm_args",
            "comments",
            "tags",
        )
        help_texts = {"hostname": "Router hostname (must be resolvable) or IP address"}


class RouterBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=Router.objects.all(), widget=forms.MultipleHiddenInput
    )
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
        label="Local AS",
    )
    platform = DynamicModelChoiceField(required=False, queryset=Platform.objects.all())
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(DeviceStatus),
        widget=StaticSelect,
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect
    )
    poll_bgp_sessions_state = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Poll BGP sessions state"
    )
    configuration_template = DynamicModelChoiceField(
        required=False, queryset=Configuration.objects.all()
    )
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ("local_context_data", "comments")


class RouterFilterForm(BootstrapMixin, forms.Form):
    model = Router
    q = forms.CharField(required=False, label="Search")
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
        label="Local AS",
    )
    platform_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Platform.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Platform",
    )
    status = forms.MultipleChoiceField(
        required=False, choices=DeviceStatus, widget=StaticSelectMultiple
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect
    )
    configuration_template_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Configuration.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Configuration",
    )
    tag = TagFilterField(model)


class RoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    type = forms.ChoiceField(choices=RoutingPolicyType, widget=StaticSelect)
    address_family = forms.ChoiceField(choices=IPFamily, widget=StaticSelect)
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = RoutingPolicy

        fields = (
            "name",
            "slug",
            "type",
            "weight",
            "address_family",
            "local_context_data",
            "comments",
            "tags",
        )


class RoutingPolicyBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=RoutingPolicy.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(RoutingPolicyType),
        widget=StaticSelect,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily, widget=StaticSelect
    )
    local_context_data = JSONField(required=False, widget=SmallTextarea)
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ("local_context_data", "comments")


class RoutingPolicyFilterForm(BootstrapMixin, forms.Form):
    model = RoutingPolicy
    q = forms.CharField(required=False, label="Search")
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
