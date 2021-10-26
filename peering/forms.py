from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from taggit.forms import TagField

from devices.models import Platform
from net.models import Connection
from netbox.api import NetBox
from utils.fields import CommentField, PasswordField, SlugField, TextareaField
from utils.forms import (
    AddRemoveTagsForm,
    BootstrapMixin,
    BulkEditForm,
    CustomNullBooleanSelect,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    JSONField,
    SmallTextarea,
    StaticSelect,
    StaticSelectMultiple,
    TagFilterField,
    add_blank_choice,
)

from .constants import ASN_MAX, ASN_MIN
from .enums import (
    BGPRelationship,
    CommunityType,
    DeviceState,
    IPFamily,
    RoutingPolicyType,
)
from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)


class TemplateField(TextareaField):
    """
    A textarea dedicated for template. Note that it does not actually do anything
    special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        label = kwargs.pop("label", "Template")
        super().__init__(
            label=label,
            help_text='<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templating/" target="_blank">Jinja2 template</a> syntax is supported',
            *args,
            **kwargs,
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
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = AutonomousSystem
        fields = (
            "asn",
            "name",
            "name_peeringdb_sync",
            "contact_name",
            "contact_phone",
            "contact_email",
            "irr_as_set",
            "irr_as_set_peeringdb_sync",
            "ipv6_max_prefixes",
            "ipv6_max_prefixes_peeringdb_sync",
            "ipv4_max_prefixes",
            "ipv4_max_prefixes_peeringdb_sync",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
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
        help_text="Friendly unique shorthand used for URL and config. Change Warning: May result in change of Operational State on a Router if being used in config generation",
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
    tags = TagField(required=False)

    class Meta:
        model = BGPGroup
        fields = (
            "name",
            "slug",
            "comments",
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "check_bgp_session_states",
            "tags",
        )
        labels = {"check_bgp_session_states": "Poll peering session states"}
        help_texts = {
            "name": "Full name of the BGP group",
            "check_bgp_session_states": "If enabled, the state of peering sessions will be polled.",
        }


class BGPGroupBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=BGPGroup.objects.all(), widget=forms.MultipleHiddenInput
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
        nullable_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "comments",
        ]


class BGPGroupFilterForm(BootstrapMixin, forms.Form):
    model = BGPGroup
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)


class CommunityForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    type = forms.ChoiceField(
        choices=add_blank_choice(CommunityType.choices),
        widget=StaticSelect,
        help_text="Ingress to tag received routes or Egress to tag advertised routes",
    )
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Community

        fields = ("name", "value", "slug", "type", "comments", "tags")
        help_texts = {
            "value": 'Community (<a target="_blank" href="https://tools.ietf.org/html/rfc1997">RFC1997</a>), Extended Community (<a target="_blank" href="https://tools.ietf.org/html/rfc4360">RFC4360</a>) or Large Community (<a target="_blank" href="https://tools.ietf.org/html/rfc8092">RFC8092</a>)'
        }


class CommunityBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=Community.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType.choices),
        widget=StaticSelect,
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comments"]


class CommunityFilterForm(BootstrapMixin, forms.Form):
    model = Community
    q = forms.CharField(required=False, label="Search")
    type = forms.MultipleChoiceField(
        required=False, choices=CommunityType.choices, widget=StaticSelectMultiple
    )
    tag = TagFilterField(model)


class ConfigurationForm(BootstrapMixin, forms.ModelForm):
    template = TemplateField()
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Configuration
        fields = (
            "name",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        )


class ConfigurationFilterForm(BootstrapMixin, forms.Form):
    model = Configuration
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)


class DirectPeeringSessionForm(BootstrapMixin, forms.ModelForm):
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
    )
    autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes")
    )
    bgp_group = DynamicModelChoiceField(
        required=False, queryset=BGPGroup.objects.all(), label="BGP Group"
    )
    relationship = forms.ChoiceField(
        choices=BGPRelationship.choices, widget=StaticSelect
    )
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
            "relationship",
            "ip_address",
            "password",
            "multihop_ttl",
            "enabled",
            "router",
            "import_routing_policies",
            "export_routing_policies",
            "comments",
            "tags",
        )
        labels = {"local_ip_address": "Local IP Address", "ip_address": "IP Address"}
        help_texts = {
            "local_ip_address": "IPv6 or IPv4 address",
            "ip_address": "IPv6 or IPv4 address",
            "enabled": "Should this session be enabled?",
        }

    def clean(self):
        cleaned_data = super().clean()

        # Make sure that both local and remote IP addresses are from the same family
        if cleaned_data["local_ip_address"] and (
            cleaned_data["local_ip_address"].version
            != cleaned_data["ip_address"].version
        ):
            raise ValidationError(
                "Local and remote IP addresses must belong to the same address family."
            )

        # Make sure that routing policies are compatible (address family)
        for policy in cleaned_data["import_routing_policies"].union(
            cleaned_data["export_routing_policies"]
        ):
            if (
                policy.address_family != IPFamily.ALL
                and policy.address_family != cleaned_data["ip_address"].version
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
    )
    enabled = forms.NullBooleanField(
        required=False, label="Enable", widget=CustomNullBooleanSelect
    )
    relationship = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(BGPRelationship.choices),
        widget=StaticSelect,
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
    comments = CommentField()

    class Meta:
        nullable_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "router",
            "comments",
        ]


class DirectPeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = DirectPeeringSession
    q = forms.CharField(required=False, label="Search")
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
        to_field_name="pk",
        label="Local autonomous system",
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
        required=False, choices=IPFamily.choices, widget=StaticSelect
    )
    enabled = forms.NullBooleanField(required=False, widget=CustomNullBooleanSelect)
    relationship = forms.MultipleChoiceField(
        required=False, choices=BGPRelationship.choices, widget=StaticSelectMultiple
    )
    router_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Router.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Router",
    )
    tag = TagFilterField(model)


class EmailForm(BootstrapMixin, forms.ModelForm):
    subject = forms.CharField(
        help_text='<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templating/" target="_blank">Jinja2 template</a> syntax is supported'
    )
    template = TemplateField(label="Body")
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Email
        fields = (
            "name",
            "subject",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        )


class EmailFilterForm(BootstrapMixin, forms.Form):
    model = Configuration
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)


class InternetExchangeForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(
        max_length=255,
        help_text="Friendly unique shorthand used for URL and config. Change Warning: May result in change of Operational State on a Router if being used in config generation",
    )
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
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
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = InternetExchange
        fields = (
            "name",
            "slug",
            "local_autonomous_system",
            "communities",
            "import_routing_policies",
            "export_routing_policies",
            "check_bgp_session_states",
            "comments",
            "tags",
        )
        labels = {"check_bgp_session_states": "Poll peering session states"}
        help_texts = {
            "name": "Full name of the Internet Exchange point",
            "check_bgp_session_states": "If enabled, with a usable router, the state of peering sessions will be polled.",
        }


class InternetExchangeBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=InternetExchange.objects.all(), widget=forms.MultipleHiddenInput
    )
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
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
    check_bgp_session_states = forms.NullBooleanField(
        required=False,
        label="Poll peering session states",
        widget=CustomNullBooleanSelect,
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "comments",
        ]


class InternetExchangePeeringDBForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.fields["peeringdb_ixlan"].widget = forms.HiddenInput()

    class Meta:
        model = InternetExchange
        fields = (
            "peeringdb_ixlan",
            "local_autonomous_system",
            "name",
            "slug",
        )
        help_texts = {"name": "Full name of the Internet Exchange point"}


class InternetExchangeFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchange
    q = forms.CharField(required=False, label="Search")
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
        label="Local autonomous system",
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
    is_route_server = forms.NullBooleanField(
        required=False, label="Route server", widget=CustomNullBooleanSelect
    )
    enabled = forms.NullBooleanField(required=False, widget=CustomNullBooleanSelect)
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
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "comments",
        ]


class InternetExchangePeeringSessionForm(BootstrapMixin, forms.ModelForm):
    autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes")
    )
    ixp_connection = DynamicModelChoiceField(
        queryset=Connection.objects.all(),
        label="IXP connection",
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
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = InternetExchangePeeringSession
        fields = (
            "service_reference",
            "autonomous_system",
            "ixp_connection",
            "ip_address",
            "password",
            "multihop_ttl",
            "is_route_server",
            "enabled",
            "import_routing_policies",
            "export_routing_policies",
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
        required=False, choices=IPFamily.choices, widget=StaticSelect
    )
    is_route_server = forms.NullBooleanField(
        required=False, label="Route server", widget=CustomNullBooleanSelect
    )
    enabled = forms.NullBooleanField(required=False, widget=CustomNullBooleanSelect)
    tag = TagFilterField(model)


class RouterForm(BootstrapMixin, forms.ModelForm):
    netbox_device_id = forms.IntegerField(label="NetBox device", initial=0)
    platform = DynamicModelChoiceField(required=False, queryset=Platform.objects.all())
    configuration_template = DynamicModelChoiceField(
        required=False,
        queryset=Configuration.objects.all(),
        label="Configuration",
        help_text="Template used to generate device configuration",
    )
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
    )
    config_context = JSONField(
        required=False, label="Config context", widget=SmallTextarea
    )
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
    device_state = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(DeviceState.choices),
        widget=StaticSelect,
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
            "encrypt_passwords",
            "device_state",
            "configuration_template",
            "local_autonomous_system",
            "config_context",
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
    )
    platform = DynamicModelChoiceField(required=False, queryset=Platform.objects.all())
    encrypt_passwords = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect
    )
    configuration_template = DynamicModelChoiceField(
        required=False, queryset=Configuration.objects.all()
    )
    device_state = forms.ChoiceField(
        required=False,
        initial=DeviceState.ENABLED,
        choices=add_blank_choice(DeviceState.choices),
        widget=StaticSelect,
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comments"]


class RouterFilterForm(BootstrapMixin, forms.Form):
    model = Router
    q = forms.CharField(required=False, label="Search")
    local_autonomous_system_id = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.defer("prefixes"),
        query_params={"affiliated": True},
        label="Local autonomous system",
    )
    platform_id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Platform.objects.all(),
        to_field_name="pk",
        null_option="None",
        label="Platform",
    )
    device_state = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(DeviceState.choices),
        widget=StaticSelect,
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
    type = forms.ChoiceField(choices=RoutingPolicyType.choices, widget=StaticSelect)
    address_family = forms.ChoiceField(choices=IPFamily.choices, widget=StaticSelect)
    config_context = JSONField(
        required=False, label="Config context", widget=SmallTextarea
    )
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
            "config_context",
            "comments",
            "tags",
        )


class RoutingPolicyBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=RoutingPolicy.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(RoutingPolicyType.choices),
        widget=StaticSelect,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily.choices, widget=StaticSelect
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comments"]


class RoutingPolicyFilterForm(BootstrapMixin, forms.Form):
    model = RoutingPolicy
    q = forms.CharField(required=False, label="Search")
    type = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(RoutingPolicyType.choices),
        widget=StaticSelectMultiple,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=add_blank_choice(IPFamily.choices), widget=StaticSelect
    )
    tag = TagFilterField(model)
