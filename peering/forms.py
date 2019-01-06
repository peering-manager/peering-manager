from django import forms
from django.conf import settings

from .constants import (
    BGP_RELATIONSHIP_CHOICES,
    COMMUNITY_TYPE_CHOICES,
    PLATFORM_CHOICES,
    ROUTING_POLICY_TYPE_CHOICES,
    ROUTING_POLICY_TYPE_EXPORT,
    ROUTING_POLICY_TYPE_IMPORT,
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
    CSVChoiceField,
    FilterChoiceField,
    PasswordField,
    SlugField,
    SmallTextarea,
    TextareaField,
    YesNoField,
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
    irr_as_set_peeringdb_sync = YesNoField(required=False, label="IRR AS-SET")
    ipv6_max_prefixes_peeringdb_sync = YesNoField(
        required=False, label="IPv6 Max Prefixes"
    )
    ipv4_max_prefixes_peeringdb_sync = YesNoField(
        required=False, label="IPv4 Max Prefixes"
    )
    comment = CommentField()

    class Meta:
        model = AutonomousSystem
        fields = (
            "asn",
            "name",
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
            "comment": "Comments",
        }
        help_texts = {
            "asn": "BGP autonomous system number (32-bit capable)",
            "name": "Full name of the AS",
        }


class AutonomousSystemCSVForm(forms.ModelForm):
    class Meta:
        model = AutonomousSystem

        fields = (
            "asn",
            "name",
            "irr_as_set",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
            "comment",
        )
        labels = {
            "asn": "ASN",
            "irr_as_set": "IRR AS-SET",
            "ipv6_max_prefixes": "IPv6 Max Prefixes",
            "ipv4_max_prefixes": "IPv4 Max Prefixes",
            "comment": "Comments",
        }
        help_texts = {
            "asn": "BGP autonomous system number (32-bit capable)",
            "name": "Full name of the AS",
        }


class AutonomousSystemImportFromPeeringDBForm(BootstrapMixin, forms.Form):
    model = AutonomousSystem
    asn = forms.IntegerField(
        label="ASN", help_text="BGP autonomous system number (32-bit capable)"
    )
    comment = CommentField()


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


class CommunityCSVForm(BootstrapMixin, forms.ModelForm):
    type = CSVChoiceField(
        choices=COMMUNITY_TYPE_CHOICES,
        required=False,
        help_text="Ingress to tag received routes or Egress to tag advertised routes",
    )

    class Meta:
        model = Community

        fields = ("name", "value", "type", "comment")
        labels = {"comment": "Comments"}
        help_texts = {"value": "Community (RFC1997) or Large Community (RFC8092)"}


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
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
    )
    password = PasswordField(required=False, render_value=True)
    enabled = YesNoField(required=False, label="Enabled")
    comment = CommentField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["autonomous_system"].widget.attrs["data-live-search"] = "true"

    class Meta:
        model = DirectPeeringSession
        fields = (
            "local_asn",
            "autonomous_system",
            "relationship",
            "ip_address",
            "password",
            "enabled",
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
        }


class DirectPeeringSessionBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=DirectPeeringSession.objects.all(), widget=forms.MultipleHiddenInput
    )
    enabled = YesNoField(required=False, label="Enable")
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
    )
    comment = CommentField()


class DirectPeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = DirectPeeringSession
    q = forms.CharField(required=False, label="Search")
    local_asn = forms.IntegerField(required=False, label="Local ASN")
    ip_address = forms.CharField(required=False, label="IP Address")
    ip_version = forms.IntegerField(
        required=False,
        label="IP Version",
        widget=forms.Select(choices=[(0, "---------"), (6, "IPv6"), (4, "IPv4")]),
    )
    enabled = YesNoField(required=False, label="Enabled")
    relationship = forms.MultipleChoiceField(
        choices=BGP_RELATIONSHIP_CHOICES, required=False
    )


class DirectPeeringSessionRoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
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
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
    )
    check_bgp_session_states = forms.ChoiceField(
        required=False,
        label="Check For Peering Session States",
        help_text="If enabled, with a usable router, the state of peering sessions will be updated.",
        choices=((True, "Yes"), (False, "No")),
        widget=forms.Select(),
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
            "comment": "Comments",
        }
        help_texts = {
            "peeringdb_id": "The PeeringDB ID for the IX connection (can be left empty)",
            "name": "Full name of the Internet Exchange point",
            "ipv6_address": "IPv6 Address used to peer",
            "ipv4_address": "IPv4 Address used to peer",
            "configuration_template": "Template for configuration generation",
            "router": "Router connected to the Internet Exchange point",
        }


class InternetExchangeBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=InternetExchange.objects.all(), widget=forms.MultipleHiddenInput
    )
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
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


class InternetExchangeCSVForm(forms.ModelForm):
    slug = SlugField()

    class Meta:
        model = InternetExchange
        fields = (
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
        help_texts = {
            "name": "Full name of the Internet Exchange point",
            "ipv6_address": "IPv6 Address used to peer",
            "ipv4_address": "IPv4 Address used to peer",
            "configuration_template": "Template for configuration generation",
            "router": "Router connected to the Internet Exchange point",
            "check_bgp_session_states": "If enabled, with a usable router, the state of peering sessions will be updated.",
        }


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
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
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
    ipv6_address = forms.CharField(required=False, label="IPv6 Address")
    ipv4_address = forms.CharField(required=False, label="IPv4 Address")
    import_routing_policies = FilterChoiceField(
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
        to_field_name="pk",
    )
    export_routing_policies = FilterChoiceField(
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
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
    is_route_server = YesNoField(required=False, label="Route Server")
    enabled = YesNoField(required=False, label="Enable")
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
    )
    comment = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comment"]


class InternetExchangePeeringSessionForm(BootstrapMixin, forms.ModelForm):
    password = PasswordField(required=False, render_value=True)
    is_route_server = YesNoField(
        required=False,
        label="Route Server",
        help_text="Define if this session is with a route server",
    )
    enabled = YesNoField(required=False, help_text="Set this session as enabled")
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
    )
    comment = CommentField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["autonomous_system"].widget.attrs["data-live-search"] = "true"

    class Meta:
        model = InternetExchangePeeringSession
        fields = (
            "autonomous_system",
            "internet_exchange",
            "ip_address",
            "password",
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
        }
        help_texts = {"ip_address": "IPv6 or IPv4 address"}


class InternetExchangePeeringSessionFilterForm(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    autonomous_system__asn = forms.IntegerField(required=False, label="ASN")
    autonomous_system__name = forms.CharField(required=False, label="AS Name")
    internet_exchange__name = forms.CharField(required=False, label="IX Name")
    ip_address = forms.CharField(required=False, label="IP Address")
    ip_version = forms.IntegerField(
        required=False,
        label="IP Version",
        widget=forms.Select(choices=[(0, "---------"), (6, "IPv6"), (4, "IPv4")]),
    )
    is_route_server = YesNoField(required=False, label="Route Server")
    enabled = YesNoField(required=False, label="Enabled")


class InternetExchangePeeringSessionFilterFormForIX(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    autonomous_system__asn = forms.IntegerField(required=False, label="ASN")
    autonomous_system__name = forms.CharField(required=False, label="AS Name")
    ip_address = forms.CharField(required=False, label="IP Address")
    ip_version = forms.IntegerField(
        required=False,
        label="IP Version",
        widget=forms.Select(choices=[(0, "---------"), (6, "IPv6"), (4, "IPv4")]),
    )
    is_route_server = YesNoField(required=False, label="Route Server")
    enabled = YesNoField(required=False, label="Enabled")


class InternetExchangePeeringSessionFilterFormForAS(BootstrapMixin, forms.Form):
    model = InternetExchangePeeringSession
    q = forms.CharField(required=False, label="Search")
    ip_address = forms.CharField(required=False, label="IP Address")
    ip_version = forms.IntegerField(
        required=False,
        label="IP Version",
        widget=forms.Select(choices=[(0, "---------"), (6, "IPv6"), (4, "IPv4")]),
    )
    is_route_server = YesNoField(required=False, label="Route Server")
    enabled = YesNoField(required=False, label="Enabled")
    internet_exchange__slug = FilterChoiceField(
        queryset=InternetExchange.objects.all(),
        to_field_name="slug",
        label="Internet Exchange",
    )


class InternetExchangePeeringSessionRoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    import_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_IMPORT),
    )
    export_routing_policies = FilterChoiceField(
        required=False,
        queryset=RoutingPolicy.objects.filter(type=ROUTING_POLICY_TYPE_EXPORT),
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

        fields = ("netbox_device_id", "name", "hostname", "platform", "comment")
        labels = {"comment": "Comments"}
        help_texts = {"hostname": "Router hostname (must be resolvable) or IP address"}


class RouterBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=Router.objects.all(), widget=forms.MultipleHiddenInput
    )
    platform = forms.ChoiceField(
        choices=add_blank_choice(PLATFORM_CHOICES), required=False
    )
    comment = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comment"]


class RouterCSVForm(BootstrapMixin, forms.ModelForm):
    platform = CSVChoiceField(
        choices=PLATFORM_CHOICES,
        required=False,
        help_text="The router platform, used to interact with it",
    )

    class Meta:
        model = Router

        fields = ("name", "hostname", "platform", "comment")
        labels = {"comment": "Comments"}
        help_texts = {"hostname": "Router hostname (must be resolvable) or IP address"}


class RouterFilterForm(BootstrapMixin, forms.Form):
    model = Router
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="Router Name")
    hostname = forms.CharField(required=False, label="Router Hostname")
    platform = forms.MultipleChoiceField(choices=PLATFORM_CHOICES, required=False)


class RoutingPolicyForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()
    comment = CommentField()

    class Meta:
        model = RoutingPolicy

        fields = ("name", "slug", "type", "comment")
        labels = {"comment": "Comments"}


class RoutingPolicyBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = FilterChoiceField(
        queryset=RoutingPolicy.objects.all(), widget=forms.MultipleHiddenInput
    )
    type = forms.ChoiceField(
        choices=add_blank_choice(ROUTING_POLICY_TYPE_CHOICES), required=False
    )
    comment = CommentField(widget=SmallTextarea)

    class Meta:
        nullable_fields = ["comment"]


class RoutingPolicyCSVForm(BootstrapMixin, forms.ModelForm):
    type = CSVChoiceField(choices=ROUTING_POLICY_TYPE_CHOICES, required=False)

    class Meta:
        model = RoutingPolicy

        fields = ("name", "slug", "type", "comment")
        labels = {"comment": "Comments"}


class RoutingPolicyFilterForm(BootstrapMixin, forms.Form):
    model = RoutingPolicy
    q = forms.CharField(required=False, label="Search")
    name = forms.CharField(required=False, label="Routing Policy Name")
    type = forms.MultipleChoiceField(
        choices=ROUTING_POLICY_TYPE_CHOICES, required=False
    )
