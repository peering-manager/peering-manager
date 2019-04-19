from django import forms
from django.db.models import Q
from django.conf import settings

from .constants import (
    BGP_RELATIONSHIP_CHOICES,
    COMMUNITY_TYPE_CHOICES,
    IP_FAMILY_CHOICES,
    PLATFORM_CHOICES,
    ROUTING_POLICY_TYPE_CHOICES,
    ROUTING_POLICY_TYPE_EXPORT,
    ROUTING_POLICY_TYPE_IMPORT,
    ROUTING_POLICY_TYPE_IMPORT_EXPORT,
)
from .models import (
    AutonomousSystem,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from netbox.api import NetBox
from peeringdb.models import PeerRecord
from utils.forms import (
    BulkEditForm,
    BootstrapMixin,
    CustomNullBooleanSelect,
    FilterChoiceField,
    PasswordField,
    SlugField,
    SmallTextarea,
    TextareaField,
    add_blank_choice,
)


class CommentField(TextareaField):
    """
    A textarea with support for GitHub-Flavored Markdown. Note that it does not
    actually do anything special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            label="Comments",
            help_text='<i class="fab fa-markdown"></i> <a href="https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet" target="_blank">GitHub-Flavored Markdown</a> syntax is supported',
            *args,
            **kwargs
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
            **kwargs
        )


class AutonomousSystemForm(BootstrapMixin, forms.ModelForm):
    comment = CommentField()

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
            "comment",
        )
        labels = {
            "asn": "ASN",
            "irr_as_set": "IRR AS-SET",
            "ipv6_max_prefixes": "IPv6 Max Prefixes",
            "ipv4_max_prefixes": "IPv4 Max Prefixes",
            "irr_as_set_peeringdb_sync": "IRR AS-SET",
            "ipv6_max_prefixes_peeringdb_sync": "IPv6 Max Prefixes",
            "ipv4_max_prefixes_peeringdb_sync": "IPv4 Max Prefixes",
            "comment": "Comments",
        }
        help_texts = {
            "asn": "BGP autonomous system number (32-bit capable)",
            "name": "Full name of the AS",
        }


class AutonomousSystemFilterForm(BootstrapMixin, forms.Form):
    model = AutonomousSystem
    q = forms.CharField(required=False, label="Search")
    asn = forms.IntegerField(required=False, label="ASN")
    name = forms.CharField(required=False, label="AS Name")
    irr_as_set = forms.CharField(required=False, label="IRR AS-SET")
    ipv6_max_prefixes = forms.IntegerField(required=False, label="IPv6 Max Prefixes")
    ipv4_max_prefixes = forms.IntegerField(required=False, label="IPv4 Max Prefixes")


class CommunityForm(BootstrapMixin, forms.ModelForm):
    comment = CommentField()

    class Meta:
        model = Community

        fields = ("name", "value", "type", "comment")
        labels = {"comment": "Comments"}
        help_texts = {
            "value": "Community (RFC1997) or Large Community (RFC8092)",
            "type": "Ingress to tag received routes or Egress to tag advertised routes",
        }


class CommunityBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=Community.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        choices=add_blank_choice(COMMUNITY_TYPE_CHOICES), required=False
    )
    comment = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comment"]


class CommunityFilterForm(BootstrapMixin, forms.Form):
    model = Community
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="Name")
    value = forms.CharField(required=False, label="Value")
    type = forms.MultipleChoiceField(choices=COMMUNITY_TYPE_CHOICES, required=False)


class ConfigurationTemplateForm(BootstrapMixin, forms.ModelForm):
    template = TemplateField()

    class Meta:
        model = ConfigurationTemplate
        fields = ("name", "template", "comment")
        labels = {"comment": "Comments"}


class ConfigurationTemplateFilterForm(BootstrapMixin, forms.Form):
    model = ConfigurationTemplate
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="Name")


class DirectPeeringSessionForm(BootstrapMixin, forms.ModelForm):
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    password = PasswordField(required=False, render_value=True)
    comment = CommentField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["autonomous_system"].widget.attrs["data-live-search"] = "true"

    def clean(self):
        # Do the regular cleanup
        cleaned_data = super().clean()

        # This should be cleaned up, ready to be used
        password = cleaned_data["password"]
        router = cleaned_data["router"]

        # Process to password check/encryption if we have what we need
        if router and password:
            # Encrypt the password only if it is not already
            cleaned_data["password"] = router.encrypt_string(password)

        return cleaned_data

    class Meta:
        model = DirectPeeringSession
        fields = (
            "local_asn",
            "autonomous_system",
            "relationship",
            "ip_address",
            "password",
            "multihop_ttl",
            "enabled",
            "router",
            "import_routing_policies",
            "export_routing_policies",
            "comment",
        )
        labels = {
            "local_asn": "Local ASN",
            "autonomous_system": "AS",
            "ip_address": "IP Address",
            "comment": "Comments",
        }
        help_texts = {
            "local_asn": "ASN to be used locally, defaults to {}".format(
                settings.MY_ASN
            ),
            "ip_address": "IPv6 or IPv4 address",
            "enabled": "Should this session be enabled?",
            "router": "Router on which this session is configured",
        }


class DirectPeeringSessionBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=DirectPeeringSession.objects.all(), widget=forms.MultipleHiddenInput
    )
    enabled = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Enable"
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    router = forms.ModelChoiceField(required=False, queryset=Router.objects.all())
    comment = CommentField()

    class Meta:
        nullable_fields = ["router", "comment"]


class DirectPeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = DirectPeeringSession
    q = forms.CharField(required=False, label="Search")
    local_asn = forms.IntegerField(required=False, label="Local ASN")
    address_family = forms.ChoiceField(required=False, choices=IP_FAMILY_CHOICES)
    enabled = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Enabled"
    )
    relationship = forms.MultipleChoiceField(
        choices=BGP_RELATIONSHIP_CHOICES, required=False
    )
    router = FilterChoiceField(
        queryset=Router.objects.all(), to_field_name="pk", null_label="-- None --"
    )


class DirectPeeringSessionRoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )

    class Meta:
        model = InternetExchange
        fields = ("export_routing_policies", "import_routing_policies")

    def __init__(self, *args, **kwargs):
        if kwargs.get("instance"):
            # Get the session object and remove it from kwargs in order to
            # avoid propagating when calling super
            instance = kwargs.pop("instance")
            # Prepare initial communities
            initial = kwargs.setdefault("initial", {})
            # Add primary key for each routing policy
            initial["export_routing_policies"] = [
                p.pk for p in instance.export_routing_policies.all()
            ]
            initial["import_routing_policies"] = [
                p.pk for p in instance.import_routing_policies.all()
            ]

        super().__init__(*args, **kwargs)

    def save(self):
        instance = forms.ModelForm.save(self)
        instance.export_routing_policies.clear()
        instance.import_routing_policies.clear()

        for routing_policy in self.cleaned_data["export_routing_policies"]:
            instance.export_routing_policies.add(routing_policy)
        for routing_policy in self.cleaned_data["import_routing_policies"]:
            instance.import_routing_policies.add(routing_policy)


class InternetExchangeForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    comment = CommentField()

    class Meta:
        model = InternetExchange
        fields = (
            "peeringdb_id",
            "name",
            "slug",
            "ipv6_address",
            "ipv4_address",
            "import_routing_policies",
            "export_routing_policies",
            "configuration_template",
            "router",
            "check_bgp_session_states",
            "comment",
        )
        labels = {
            "peeringdb_id": "PeeringDB ID",
            "ipv6_address": "IPv6 Address",
            "ipv4_address": "IPv4 Address",
            "check_bgp_session_states": "Check Peering Session States",
            "comment": "Comments",
        }
        help_texts = {
            "peeringdb_id": "The PeeringDB ID for the IX connection (can be left empty)",
            "name": "Full name of the Internet Exchange point",
            "ipv6_address": "IPv6 Address used to peer",
            "ipv4_address": "IPv4 Address used to peer",
            "configuration_template": "Template for configuration generation",
            "router": "Router connected to the Internet Exchange point",
            "check_bgp_session_states": "If enabled, with a usable router, the state of peering sessions will be updated.",
        }


class InternetExchangeBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=InternetExchange.objects.all(), widget=forms.MultipleHiddenInput
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    configuration_template = forms.ModelChoiceField(
        required=False, queryset=ConfigurationTemplate.objects.all()
    )
    router = forms.ModelChoiceField(required=False, queryset=Router.objects.all())
    comment = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["configuration_template", "router", "comment"]


class InternetExchangePeeringDBForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()

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


class InternetExchangeCommunityForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = InternetExchange
        fields = ("communities",)

    def __init__(self, *args, **kwargs):
        if kwargs.get("instance"):
            # Get the IX object and remove it from kwargs in order to avoid
            # propagating when calling super
            instance = kwargs.pop("instance")
            # Prepare initial communities
            initial = kwargs.setdefault("initial", {})
            # Add primary key for each community
            initial["communities"] = [c.pk for c in instance.communities.all()]

        super().__init__(*args, **kwargs)

    def save(self):
        instance = forms.ModelForm.save(self)
        instance.communities.clear()

        for community in self.cleaned_data["communities"]:
            instance.communities.add(community)


class InternetExchangeRoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )

    class Meta:
        model = InternetExchange
        fields = ("export_routing_policies", "import_routing_policies")

    def __init__(self, *args, **kwargs):
        if kwargs.get("instance"):
            # Get the IX object and remove it from kwargs in order to avoid
            # propagating when calling super
            instance = kwargs.pop("instance")
            # Prepare initial communities
            initial = kwargs.setdefault("initial", {})
            # Add primary key for each routing policy
            initial["export_routing_policies"] = [
                p.pk for p in instance.export_routing_policies.all()
            ]
            initial["import_routing_policies"] = [
                p.pk for p in instance.import_routing_policies.all()
            ]

        super().__init__(*args, **kwargs)

    def save(self):
        instance = forms.ModelForm.save(self)
        instance.export_routing_policies.clear()
        instance.import_routing_policies.clear()

        for routing_policy in self.cleaned_data["export_routing_policies"]:
            instance.export_routing_policies.add(routing_policy)
        for routing_policy in self.cleaned_data["import_routing_policies"]:
            instance.import_routing_policies.add(routing_policy)


class InternetExchangeFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchange
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="IX Name")
    import_routing_policies = FilterChoiceField(
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
        to_field_name="pk",
    )
    export_routing_policies = FilterChoiceField(
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
        to_field_name="pk",
    )
    configuration_template = FilterChoiceField(
        queryset=ConfigurationTemplate.objects.all(),
        to_field_name="pk",
        null_label="-- None --",
    )
    router = FilterChoiceField(
        queryset=Router.objects.all(), to_field_name="pk", null_label="-- None --"
    )


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


class InternetExchangePeeringSessionBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=InternetExchangePeeringSession.objects.all(),
        widget=forms.MultipleHiddenInput,
    )
    is_route_server = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Route Server"
    )
    enabled = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Enable"
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    comment = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comment"]


class InternetExchangePeeringSessionForm(BootstrapMixin, forms.ModelForm):
    password = PasswordField(required=False, render_value=True)
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    comment = CommentField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["autonomous_system"].widget.attrs["data-live-search"] = "true"

    def clean(self):
        # Do the regular cleanup
        cleaned_data = super().clean()

        # This should be cleaned up, ready to be used
        password = cleaned_data["password"]
        internet_exchange = cleaned_data["internet_exchange"]

        # Process to password check/encryption if we have what we need
        if internet_exchange.router and password:
            # Encrypt the password only if it is not already
            cleaned_data["password"] = internet_exchange.router.encrypt_string(password)

        return cleaned_data

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
            "comment",
        )
        labels = {
            "autonomous_system": "AS",
            "internet_exchange": "IX",
            "ip_address": "IP Address",
            "is_route_server": "Route Server",
        }
        help_texts = {
            "ip_address": "IPv6 or IPv4 address",
            "is_route_server": "Define if this session is with a route server",
        }


class InternetExchangePeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    autonomous_system__asn = forms.IntegerField(required=False, label="ASN")
    autonomous_system__name = forms.CharField(required=False, label="AS Name")
    internet_exchange__name = forms.CharField(required=False, label="IX Name")
    address_family = forms.ChoiceField(required=False, choices=IP_FAMILY_CHOICES)
    is_route_server = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Route Server"
    )
    enabled = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Enabled"
    )


class InternetExchangePeeringSessionFilterFormForIX(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    autonomous_system__asn = forms.IntegerField(required=False, label="ASN")
    autonomous_system__name = forms.CharField(required=False, label="AS Name")
    address_family = forms.ChoiceField(required=False, choices=IP_FAMILY_CHOICES)
    is_route_server = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Route Server"
    )
    enabled = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Enabled"
    )


class InternetExchangePeeringSessionFilterFormForAS(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    address_family = forms.ChoiceField(required=False, choices=IP_FAMILY_CHOICES)
    is_route_server = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Route Server"
    )
    enabled = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Enabled"
    )
    internet_exchange__slug = FilterChoiceField(
        queryset=InternetExchange.objects.all(),
        to_field_name="slug",
        label="Internet Exchange",
    )


class InternetExchangePeeringSessionRoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_IMPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(
            Q(type=ROUTING_POLICY_TYPE_EXPORT)
            | Q(type=ROUTING_POLICY_TYPE_IMPORT_EXPORT)
        ),
    )

    class Meta:
        model = InternetExchange
        fields = ("export_routing_policies", "import_routing_policies")

    def __init__(self, *args, **kwargs):
        if kwargs.get("instance"):
            # Get the session object and remove it from kwargs in order to
            # avoid propagating when calling super
            instance = kwargs.pop("instance")
            # Prepare initial communities
            initial = kwargs.setdefault("initial", {})
            # Add primary key for each routing policy
            initial["export_routing_policies"] = [
                p.pk for p in instance.export_routing_policies.all()
            ]
            initial["import_routing_policies"] = [
                p.pk for p in instance.import_routing_policies.all()
            ]

        super().__init__(*args, **kwargs)

    def save(self):
        instance = forms.ModelForm.save(self)
        instance.export_routing_policies.clear()
        instance.import_routing_policies.clear()

        for routing_policy in self.cleaned_data["export_routing_policies"]:
            instance.export_routing_policies.add(routing_policy)
        for routing_policy in self.cleaned_data["import_routing_policies"]:
            instance.import_routing_policies.add(routing_policy)


class RouterForm(BootstrapMixin, forms.ModelForm):
    netbox_device_id = forms.IntegerField(label="NetBox Device", initial=0)
    comment = CommentField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if settings.NETBOX_API:
            self.fields["netbox_device_id"] = forms.ChoiceField(
                label="NetBox Device",
                choices=[(0, "--------")]
                + [
                    (device["id"], device["display_name"])
                    for device in NetBox().get_devices()
                ],
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
            "name",
            "hostname",
            "platform",
            "encrypt_passwords",
            "comment",
        )
        labels = {"comment": "Comments"}
        help_texts = {"hostname": "Router hostname (must be resolvable) or IP address"}


class RouterBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=Router.objects.all(), widget=forms.MultipleHiddenInput
    )
    platform = forms.ChoiceField(
        choices=add_blank_choice(PLATFORM_CHOICES), required=False
    )
    encrypt_passwords = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Encrypt Passwords"
    )
    comment = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comment"]


class RouterFilterForm(BootstrapMixin, forms.Form):
    model = Router
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="Router Name")
    hostname = forms.CharField(required=False, label="Router Hostname")
    platform = forms.MultipleChoiceField(choices=PLATFORM_CHOICES, required=False)
    encrypt_passwords = forms.NullBooleanField(
        required=False, widget=CustomNullBooleanSelect, label="Encrypt Passwords"
    )


class RoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()
    comment = CommentField()

    class Meta:
        model = RoutingPolicy

        fields = ("name", "slug", "type", "weight", "address_family", "comment")
        labels = {"comment": "Comments"}


class RoutingPolicyBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=RoutingPolicy.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        choices=add_blank_choice(ROUTING_POLICY_TYPE_CHOICES), required=False
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(required=False, choices=IP_FAMILY_CHOICES)
    comment = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comment"]


class RoutingPolicyFilterForm(BootstrapMixin, forms.Form):
    model = RoutingPolicy
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="Routing Policy Name")
    type = forms.MultipleChoiceField(
        choices=ROUTING_POLICY_TYPE_CHOICES, required=False
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(required=False, choices=IP_FAMILY_CHOICES)
