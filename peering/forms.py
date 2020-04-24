from django import forms
from django.conf import settings

from taggit.forms import TagField

from .constants import (
    ASN_MAX,
    ASN_MIN,
    BGP_RELATIONSHIP_CHOICES,
    COMMUNITY_TYPE_CHOICES,
    IP_FAMILY_CHOICES,
    PLATFORM_CHOICES,
    ROUTING_POLICY_TYPE_CHOICES,
    TEMPLATE_TYPE_CHOICES,
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
    Template,
)
from netbox.api import NetBox
from utils.fields import CommentField, PasswordField, SlugField, TextareaField
from utils.forms import (
    add_blank_choice,
    AddRemoveTagsForm,
    APISelect,
    APISelectMultiple,
    BulkEditForm,
    BootstrapMixin,
    CustomNullBooleanSelect,
    FilterChoiceField,
    SmallTextarea,
    StaticSelect,
    StaticSelectMultiple,
)


class TemplateField(TextareaField):
    """
    A textarea dedicated for template. Note that it does not actually do anything
    special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            label="Template",
            help_text='<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/config-template/#configuration-template" target="_blank">Jinja2 template</a> syntax is supported',
            *args,
            **kwargs,
        )


class AutonomousSystemForm(BootstrapMixin, forms.ModelForm):
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = AutonomousSystem
        fields = (
            "asn",
            "name",
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
            "comments",
            "tags",
        )
        labels = {
            "asn": "ASN",
            "irr_as_set": "IRR AS-SET",
            "ipv6_max_prefixes": "IPv6 Max Prefixes",
            "ipv4_max_prefixes": "IPv4 Max Prefixes",
            "irr_as_set_peeringdb_sync": "IRR AS-SET",
            "ipv6_max_prefixes_peeringdb_sync": "IPv6 Max Prefixes",
            "ipv4_max_prefixes_peeringdb_sync": "IPv4 Max Prefixes",
        }
        help_texts = {
            "asn": "BGP autonomous system number (32-bit capable)",
            "name": "Full name of the AS",
        }


class AutonomousSystemFilterForm(BootstrapMixin, forms.Form):
    model = AutonomousSystem
    q = forms.CharField(required=False, label="Search")
    asn = forms.IntegerField(required=False, label="ASN")
    irr_as_set = forms.CharField(required=False, label="IRR AS-SET")
    ipv6_max_prefixes = forms.IntegerField(required=False, label="IPv6 Max Prefixes")
    ipv4_max_prefixes = forms.IntegerField(required=False, label="IPv4 Max Prefixes")


class AutonomousSystemEmailForm(BootstrapMixin, forms.Form):
    template = forms.ModelChoiceField(
        queryset=Template.objects.all(),
        widget=APISelect(
            api_url="/api/peering/templates/", query_filters={"type": "email"}
        ),
    )
    recipient = forms.ChoiceField(widget=StaticSelect, label="E-mail Recipient")
    subject = forms.CharField(label="E-mail Subject")
    body = TextareaField(label="E-mail Body")


class BGPGroupForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    comments = CommentField()
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    communities = FilterChoiceField(
        required=False,
        queryset=Community.objects.all(),
        widget=APISelectMultiple(api_url="/api/peering/communities/"),
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
        labels = {"check_bgp_session_states": "Poll Peering Session States"}
        help_texts = {
            "name": "Full name of the BGP group",
            "check_bgp_session_states": "If enabled, the state of peering sessions will be polled.",
        }


class BGPGroupBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = FilterChoiceField(
        queryset=BGPGroup.objects.all(), widget=forms.MultipleHiddenInput
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    communities = FilterChoiceField(
        required=False,
        queryset=Community.objects.all(),
        widget=APISelectMultiple(api_url="/api/peering/communities/"),
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


class CommunityForm(BootstrapMixin, forms.ModelForm):
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Community

        fields = ("name", "value", "type", "comments", "tags")
        help_texts = {
            "value": "Community (RFC1997) or Large Community (RFC8092)",
            "type": "Ingress to tag received routes or Egress to tag advertised routes",
        }


class CommunityBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = FilterChoiceField(
        queryset=Community.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(COMMUNITY_TYPE_CHOICES),
        widget=StaticSelect,
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comments"]


class CommunityFilterForm(BootstrapMixin, forms.Form):
    model = Community
    q = forms.CharField(required=False, label="Search")
    type = forms.MultipleChoiceField(
        required=False, choices=COMMUNITY_TYPE_CHOICES, widget=StaticSelectMultiple
    )


class DirectPeeringSessionForm(BootstrapMixin, forms.ModelForm):
    local_asn = forms.IntegerField(
        min_value=ASN_MIN,
        max_value=ASN_MAX,
        label="Local ASN",
        help_text=f"ASN to be used locally, defaults to {settings.MY_ASN}",
    )
    autonomous_system = forms.ModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        label="Autonomous System",
        widget=APISelect(api_url="/api/peering/autonomous-systems/"),
    )
    bgp_group = forms.ModelChoiceField(
        required=False,
        queryset=BGPGroup.objects.all(),
        label="BGP Group",
        widget=APISelect(api_url="/api/peering/bgp-groups/"),
    )
    relationship = forms.ChoiceField(
        choices=BGP_RELATIONSHIP_CHOICES, widget=StaticSelect
    )
    router = forms.ModelChoiceField(
        required=False,
        queryset=Router.objects.all(),
        widget=APISelect(api_url="/api/peering/routers/"),
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    password = PasswordField(required=False, render_value=True)
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = DirectPeeringSession
        fields = (
            "local_asn",
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
            "router": "Router on which this session is configured",
        }

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", None)
        updated = {}
        if initial:
            updated["autonomous_system"] = initial.get("autonomous_system", None)
        updated["local_asn"] = settings.MY_ASN
        kwargs.update(initial=updated)
        super().__init__(*args, **kwargs)


class DirectPeeringSessionBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = FilterChoiceField(
        queryset=DirectPeeringSession.objects.all(), widget=forms.MultipleHiddenInput
    )
    enabled = forms.NullBooleanField(
        required=False, label="Enable", widget=CustomNullBooleanSelect
    )
    relationship = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(BGP_RELATIONSHIP_CHOICES), 
        widget=StaticSelect
    )
    bgp_group = forms.ModelChoiceField(
        required=False,
        queryset=BGPGroup.objects.all(),
        label="BGP Group",
        widget=APISelect(api_url="/api/peering/bgp-groups/"),
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    router = forms.ModelChoiceField(
        required=False,
        queryset=Router.objects.all(),
        widget=APISelect(api_url="/api/peering/routers/"),
    )
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
    local_asn = forms.IntegerField(required=False, label="Local ASN")
    bgp_group = FilterChoiceField(
        queryset=BGPGroup.objects.all(),
        to_field_name="pk",
        null_label=True,
        label="BGP Group",
        widget=APISelectMultiple(api_url="/api/peering/bgp-groups/", null_option=True),
    )
    address_family = forms.ChoiceField(
        required=False, choices=IP_FAMILY_CHOICES, widget=StaticSelect
    )
    enabled = forms.NullBooleanField(
        required=False, label="Enabled", widget=CustomNullBooleanSelect
    )
    relationship = forms.MultipleChoiceField(
        required=False, choices=BGP_RELATIONSHIP_CHOICES, widget=StaticSelectMultiple
    )
    router = FilterChoiceField(
        queryset=Router.objects.all(),
        to_field_name="pk",
        null_label=True,
        widget=APISelectMultiple(api_url="/api/peering/routers/", null_option=True),
    )


class InternetExchangeForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    communities = FilterChoiceField(
        required=False,
        queryset=Community.objects.all(),
        widget=APISelectMultiple(api_url="/api/peering/communities/"),
    )
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = InternetExchange
        fields = (
            "peeringdb_id",
            "name",
            "slug",
            "ipv6_address",
            "ipv4_address",
            "communities",
            "import_routing_policies",
            "export_routing_policies",
            "router",
            "check_bgp_session_states",
            "comments",
            "tags",
        )
        labels = {
            "peeringdb_id": "PeeringDB ID",
            "ipv6_address": "IPv6 Address",
            "ipv4_address": "IPv4 Address",
            "check_bgp_session_states": "Poll Peering Session States",
        }
        help_texts = {
            "peeringdb_id": "The PeeringDB ID for the IX connection (can be left empty)",
            "name": "Full name of the Internet Exchange point",
            "ipv6_address": "IPv6 Address used to peer",
            "ipv4_address": "IPv4 Address used to peer",
            "router": "Router connected to the Internet Exchange point",
            "check_bgp_session_states": "If enabled, with a usable router, the state of peering sessions will be polled.",
        }
        widgets = {"router": APISelect(api_url="/api/peering/routers/")}


class InternetExchangeBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = FilterChoiceField(
        queryset=InternetExchange.objects.all(), widget=forms.MultipleHiddenInput
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    communities = FilterChoiceField(
        required=False,
        queryset=Community.objects.all(),
        widget=APISelectMultiple(api_url="/api/peering/communities/"),
    )
    router = forms.ModelChoiceField(
        required=False,
        queryset=Router.objects.all(),
        widget=APISelect(api_url="/api/peering/routers/"),
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "communities",
            "router",
            "comments",
        ]


class InternetExchangePeeringDBForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.fields["peeringdb_id"].widget = forms.HiddenInput()

    class Meta:
        model = InternetExchange
        fields = ("peeringdb_id", "name", "slug", "ipv6_address", "ipv4_address")
        labels = {"ipv6_address": "IPv6 Address", "ipv4_address": "IPv4 Address"}
        help_texts = {
            "name": "Full name of the Internet Exchange point",
            "ipv6_address": "IPv6 Address used to peer",
            "ipv4_address": "IPv4 Address used to peer",
        }


class InternetExchangePeeringDBFormSet(forms.BaseFormSet):
    def clean(self):
        """
        Check if slugs are uniques accross forms.
        """
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on
            # its own
            return

        slugs = []
        for form in self.forms:
            slug = form.cleaned_data["slug"]
            if slug in slugs:
                raise forms.ValidationError(
                    "Internet Exchanges must have distinct slugs."
                )
            slugs.append(slug)


class InternetExchangeFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchange
    q = forms.CharField(required=False, label="Search")
    import_routing_policies = FilterChoiceField(
        queryset=RoutingPolicy.objects.all(),
        to_field_name="pk",
        null_label=True,
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
            null_option=True,
        ),
    )
    export_routing_policies = FilterChoiceField(
        queryset=RoutingPolicy.objects.all(),
        to_field_name="pk",
        null_label=True,
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
            null_option=True,
        ),
    )
    router = FilterChoiceField(
        queryset=Router.objects.all(),
        to_field_name="pk",
        null_label=True,
        widget=APISelectMultiple(api_url="/api/peering/routers/", null_option=True),
    )


class InternetExchangePeeringSessionBulkEditForm(
    BootstrapMixin, AddRemoveTagsForm, BulkEditForm
):
    pk = FilterChoiceField(
        queryset=InternetExchangePeeringSession.objects.all(),
        widget=forms.MultipleHiddenInput,
    )
    is_route_server = forms.NullBooleanField(
        required=False, label="Route Server", widget=CustomNullBooleanSelect
    )
    enabled = forms.NullBooleanField(
        required=False, label="Enable", widget=CustomNullBooleanSelect
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "comments",
        ]


class InternetExchangePeeringSessionForm(BootstrapMixin, forms.ModelForm):
    autonomous_system = forms.ModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        label="Autonomous System",
        widget=APISelect(api_url="/api/peering/autonomous-systems/"),
    )
    password = PasswordField(required=False, render_value=True)
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "import-policy"},
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.all(),
        widget=APISelectMultiple(
            api_url="/api/peering/routing-policies/",
            query_filters={"type": "export-policy"},
        ),
    )
    comments = CommentField()
    tags = TagField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = InternetExchangePeeringSession
        fields = (
            "autonomous_system",
            "internet_exchange",
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
        labels = {
            "internet_exchange": "Internet Exchange",
            "ip_address": "IP Address",
            "is_route_server": "Route Server",
        }
        help_texts = {
            "ip_address": "IPv6 or IPv4 address",
            "is_route_server": "Define if this session is with a route server",
        }
        widgets = {
            "autonomous_system": APISelect(api_url="/api/peering/autonomous-systems/"),
            "internet_exchange": APISelect(api_url="/api/peering/internet-exchanges/"),
        }


class InternetExchangePeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    autonomous_system__id = FilterChoiceField(
        queryset=AutonomousSystem.objects.all(),
        to_field_name="pk",
        label="Autonomous System",
        null_label=True,
        widget=APISelectMultiple(api_url="/api/peering/autonomous-systems/"),
    )
    internet_exchange__id = FilterChoiceField(
        queryset=InternetExchange.objects.all(),
        to_field_name="pk",
        label="Internet Exchange",
        null_label=True,
        widget=APISelectMultiple(api_url="/api/peering/internet-exchanges/"),
    )
    address_family = forms.ChoiceField(
        required=False, choices=IP_FAMILY_CHOICES, widget=StaticSelect
    )
    is_route_server = forms.NullBooleanField(
        required=False, label="Route Server", widget=CustomNullBooleanSelect
    )
    enabled = forms.NullBooleanField(
        required=False, label="Enabled", widget=CustomNullBooleanSelect
    )


class RouterForm(BootstrapMixin, forms.ModelForm):
    netbox_device_id = forms.IntegerField(label="NetBox Device", initial=0)
    platform = forms.ChoiceField(
        required=False, choices=add_blank_choice(PLATFORM_CHOICES), widget=StaticSelect
    )
    comments = CommentField()
    tags = TagField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings.NETBOX_API:
            self.fields["netbox_device_id"] = forms.ChoiceField(
                label="NetBox Device",
                choices=[(0, "--------")]
                + [
                    (device.id, device.display_name)
                    for device in NetBox().get_devices()
                ],
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
            "configuration_template",
            "comments",
            "tags",
        )
        labels = {"use_netbox": "Use NetBox", "configuration_template": "Configuration"}
        help_texts = {
            "hostname": "Router hostname (must be resolvable) or IP address",
            "configuration_template": "Template used to generate device configuration",
        }
        widgets = {
            "configuration_template": APISelect(
                api_url="/api/peering/templates/",
                query_filters={"type": "configuration"},
            )
        }


class RouterBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = FilterChoiceField(
        queryset=Router.objects.all(), widget=forms.MultipleHiddenInput
    )
    platform = forms.ChoiceField(
        required=False, choices=add_blank_choice(PLATFORM_CHOICES), widget=StaticSelect
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False, label="Encrypt Passwords", widget=CustomNullBooleanSelect
    )
    configuration_template = forms.ModelChoiceField(
        required=False,
        queryset=Template.objects.all(),
        widget=APISelect(
            api_url="/api/peering/templates/", query_filters={"type": "configuration"}
        ),
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comments"]


class RouterFilterForm(BootstrapMixin, forms.Form):
    model = Router
    q = forms.CharField(required=False, label="Search")
    platform = forms.MultipleChoiceField(
        required=False, choices=PLATFORM_CHOICES, widget=StaticSelectMultiple
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False, label="Encrypt Passwords", widget=CustomNullBooleanSelect
    )
    configuration_template = FilterChoiceField(
        queryset=Template.objects.all(),
        to_field_name="pk",
        null_label=True,
        widget=APISelectMultiple(api_url="/api/peering/templates/", null_option=True),
    )


class RoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    type = forms.ChoiceField(choices=ROUTING_POLICY_TYPE_CHOICES, widget=StaticSelect)
    address_family = forms.ChoiceField(choices=IP_FAMILY_CHOICES, widget=StaticSelect)
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
            "comments",
            "tags",
        )


class RoutingPolicyBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = FilterChoiceField(
        queryset=RoutingPolicy.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(ROUTING_POLICY_TYPE_CHOICES),
        widget=StaticSelect,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=IP_FAMILY_CHOICES, widget=StaticSelect
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comments"]


class RoutingPolicyFilterForm(BootstrapMixin, forms.Form):
    model = RoutingPolicy
    q = forms.CharField(required=False, label="Search")
    type = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(ROUTING_POLICY_TYPE_CHOICES),
        widget=StaticSelectMultiple,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=add_blank_choice(IP_FAMILY_CHOICES), widget=StaticSelect
    )


class TemplateForm(BootstrapMixin, forms.ModelForm):
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(TEMPLATE_TYPE_CHOICES),
        widget=StaticSelect,
    )
    template = TemplateField()
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Template
        fields = ("name", "type", "template", "comments", "tags")


class TemplateFilterForm(BootstrapMixin, forms.Form):
    model = Template
    q = forms.CharField(required=False, label="Search")
    type = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(TEMPLATE_TYPE_CHOICES),
        widget=StaticSelectMultiple,
    )
