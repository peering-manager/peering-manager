from django import forms
from django.conf import settings
from django.contrib.postgres.forms.jsonb import JSONField

from taggit.forms import TagField

from .constants import ASN_MIN, ASN_MAX
from .enums import BGPRelationship, CommunityType, IPFamily, Platform, RoutingPolicyType
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
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    SmallTextarea,
    StaticSelect,
    StaticSelectMultiple,
    TagFilterField,
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
            help_text='<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templates/" target="_blank">Jinja2 template</a> syntax is supported',
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
            "comments",
            "affiliated",
            "tags",
        )
        labels = {
            "asn": "ASN",
            "irr_as_set": "IRR AS-SET",
            "ipv6_max_prefixes": "IPv6 Max Prefixes",
            "ipv4_max_prefixes": "IPv4 Max Prefixes",
            "name_peeringdb_sync": "Name",
            "irr_as_set_peeringdb_sync": "IRR AS-SET",
            "ipv6_max_prefixes_peeringdb_sync": "IPv6 Max Prefixes",
            "ipv4_max_prefixes_peeringdb_sync": "IPv4 Max Prefixes",
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
    irr_as_set = forms.CharField(required=False, label="IRR AS-SET")
    ipv6_max_prefixes = forms.IntegerField(required=False, label="IPv6 Max Prefixes")
    ipv4_max_prefixes = forms.IntegerField(required=False, label="IPv4 Max Prefixes")
    affiliated = forms.NullBooleanField(required=False, widget=CustomNullBooleanSelect)
    tag = TagFilterField(model)


class AutonomousSystemEmailForm(BootstrapMixin, forms.Form):
    email = DynamicModelChoiceField(required=False, queryset=Email.objects.all())
    recipient = forms.ChoiceField(widget=StaticSelect, label="E-mail Recipient")
    subject = forms.CharField(label="E-mail Subject")
    body = TextareaField(label="E-mail Body")


class BGPGroupForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
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
        labels = {"check_bgp_session_states": "Poll Peering Session States"}
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
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Community

        fields = ("name", "value", "slug", "type", "comments", "tags")
        help_texts = {
            "value": 'Community (<a target="_blank" href="https://tools.ietf.org/html/rfc1997">RFC1997</a>), Extended Communit (<a target="_blank" href="https://tools.ietf.org/html/rfc4360">RFC4360</a>) or Large Community (<a target="_blank" href="https://tools.ietf.org/html/rfc8092">RFC8092</a>)',
            "type": "Ingress to tag received routes or Egress to tag advertised routes",
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
        fields = ("name", "template", "comments", "tags")


class ConfigurationFilterForm(BootstrapMixin, forms.Form):
    model = Configuration
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)


class DirectPeeringSessionForm(BootstrapMixin, forms.ModelForm):
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local Autonomous System",
    )
    autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(), label="Autonomous System"
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


class DirectPeeringSessionBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=DirectPeeringSession.objects.all(), widget=forms.MultipleHiddenInput
    )
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local Autonomous System",
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
        required=False, queryset=BGPGroup.objects.all(), label="BGP Group"
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
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        to_field_name="pk",
        label="Local Autonomous System",
    )
    bgp_group = DynamicModelMultipleChoiceField(
        required=False,
        queryset=BGPGroup.objects.all(),
        to_field_name="pk",
        label="BGP Group",
        null_option="None",
    )
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily.choices, widget=StaticSelect
    )
    enabled = forms.NullBooleanField(
        required=False, label="Enabled", widget=CustomNullBooleanSelect
    )
    relationship = forms.MultipleChoiceField(
        required=False, choices=BGPRelationship.choices, widget=StaticSelectMultiple
    )
    router = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Router.objects.all(),
        to_field_name="pk",
        null_option="None",
    )
    tag = TagFilterField(model)


class EmailForm(BootstrapMixin, forms.ModelForm):
    subject = forms.CharField(
        help_text='<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templates/" target="_blank">Jinja2 template</a> syntax is supported'
    )
    template = TemplateField(label="Body")
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Email
        fields = ("name", "subject", "template", "comments", "tags")


class EmailFilterForm(BootstrapMixin, forms.Form):
    model = Configuration
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)


class InternetExchangeForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local Autonomous System",
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
    router = DynamicModelChoiceField(
        required=False,
        queryset=Router.objects.all(),
        help_text="Router connected to the Internet Exchange point",
    )
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = InternetExchange
        fields = (
            "peeringdb_id",
            "name",
            "slug",
            "local_autonomous_system",
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
            "check_bgp_session_states": "If enabled, with a usable router, the state of peering sessions will be polled.",
        }


class InternetExchangeBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=InternetExchange.objects.all(), widget=forms.MultipleHiddenInput
    )
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local Autonomous System",
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
        required=False, label="Poll BGP State", widget=CustomNullBooleanSelect
    )
    router = DynamicModelChoiceField(required=False, queryset=Router.objects.all())
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
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local Autonomous System",
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
    router = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Router.objects.all(),
        to_field_name="pk",
        null_option="None",
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
        required=False, label="Route Server", widget=CustomNullBooleanSelect
    )
    enabled = forms.NullBooleanField(
        required=False, label="Enable", widget=CustomNullBooleanSelect
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
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = [
            "import_routing_policies",
            "export_routing_policies",
            "comments",
        ]


class InternetExchangePeeringSessionForm(BootstrapMixin, forms.ModelForm):
    autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(), label="Autonomous System"
    )
    internet_exchange = DynamicModelChoiceField(
        queryset=InternetExchange.objects.all(), label="Internet Exchange"
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
        labels = {"ip_address": "IP Address", "is_route_server": "Route Server"}
        help_texts = {
            "ip_address": "IPv6 or IPv4 address",
            "is_route_server": "Define if this session is with a route server",
        }


class InternetExchangePeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    autonomous_system__id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        to_field_name="pk",
        label="Autonomous System",
    )
    internet_exchange__id = DynamicModelMultipleChoiceField(
        required=False,
        queryset=InternetExchange.objects.all(),
        to_field_name="pk",
        label="Internet Exchange",
    )
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily.choices, widget=StaticSelect
    )
    is_route_server = forms.NullBooleanField(
        required=False, label="Route Server", widget=CustomNullBooleanSelect
    )
    enabled = forms.NullBooleanField(
        required=False, label="Enabled", widget=CustomNullBooleanSelect
    )
    tag = TagFilterField(model)


class RouterForm(BootstrapMixin, forms.ModelForm):
    netbox_device_id = forms.IntegerField(label="NetBox Device", initial=0)
    platform = forms.ChoiceField(
        required=False, choices=add_blank_choice(Platform.choices), widget=StaticSelect
    )
    configuration_template = DynamicModelChoiceField(
        required=False,
        queryset=Configuration.objects.all(),
        label="Configuration",
        help_text="Template used to generate device configuration",
    )
    local_autonomous_system = DynamicModelChoiceField(
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local Autonomous System",
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
        label="Optional Arguments",
        help_text="See NAPALM's <a href='http://napalm.readthedocs.io/en/latest/support/#optional-arguments'>documentation</a> for a complete list of optional arguments",
        widget=SmallTextarea,
    )
    comments = CommentField()
    tags = TagField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings.NETBOX_API:
            self.fields["netbox_device_id"] = forms.ChoiceField(
                label="NetBox Device",
                choices=[(0, "---------")]
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
            "local_autonomous_system",
            "napalm_username",
            "napalm_password",
            "napalm_timeout",
            "napalm_args",
            "comments",
            "tags",
        )
        labels = {"use_netbox": "Use NetBox"}
        help_texts = {"hostname": "Router hostname (must be resolvable) or IP address"}


class RouterBulkEditForm(BootstrapMixin, AddRemoveTagsForm, BulkEditForm):
    pk = DynamicModelMultipleChoiceField(
        queryset=Router.objects.all(), widget=forms.MultipleHiddenInput
    )
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local Autonomous System",
    )
    platform = forms.ChoiceField(
        required=False, choices=add_blank_choice(Platform.choices), widget=StaticSelect
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False, label="Encrypt Passwords", widget=CustomNullBooleanSelect
    )
    configuration_template = DynamicModelChoiceField(
        required=False, queryset=Configuration.objects.all()
    )
    comments = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comments"]


class RouterFilterForm(BootstrapMixin, forms.Form):
    model = Router
    q = forms.CharField(required=False, label="Search")
    local_autonomous_system = DynamicModelChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        label="Local Autonomous System",
    )
    platform = forms.MultipleChoiceField(
        required=False, choices=Platform.choices, widget=StaticSelectMultiple
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False, label="Encrypt Passwords", widget=CustomNullBooleanSelect
    )
    configuration_template = DynamicModelMultipleChoiceField(
        required=False,
        queryset=Configuration.objects.all(),
        to_field_name="pk",
        null_option="None",
    )
    local_autonomous_system = DynamicModelMultipleChoiceField(
        required=False,
        queryset=AutonomousSystem.objects.all(),
        query_params={"affiliated": True},
        to_field_name="pk",
        null_option="None",
    )
    tag = TagFilterField(model)


class RoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    type = forms.ChoiceField(choices=RoutingPolicyType.choices, widget=StaticSelect)
    address_family = forms.ChoiceField(choices=IPFamily.choices, widget=StaticSelect)
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
