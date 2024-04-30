import ipaddress

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from netfields import CidrAddressField, InetAddressField, MACAddressField

from peering.fields import ASNField
from utils.validators import AddressFamilyValidator

from .enums import (
    MTU,
    AvailableVoltage,
    ContractsPolicy,
    GeneralPolicy,
    LocationsPolicy,
    Media,
    NetType,
    NetTypeMultiChoice,
    POCRole,
    Property,
    Protocol,
    Ratio,
    Region,
    Scope,
    ServiceLevels,
    Terms,
    Traffic,
    Visibility,
)

__all__ = (
    "Organization",
    "Campus",
    "Facility",
    "Carrier",
    "CarrierFacility",
    "Network",
    "InternetExchange",
    "InternetExchangeFacility",
    "IXLan",
    "IXLanPrefix",
    "NetworkContact",
    "NetworkFacility",
    "NetworkIXLan",
    "Synchronisation",
)

# A huge part of this code comes from the django_peeringdb library.
#
# https://github.com/peeringdb/django-peeringdb/
#
# It has been modified to suit Peering Manager's code base and avoid to depend on
# other libraries.


class URLField(models.URLField):
    default_validators = [URLValidator(schemes=["http", "https", "telnet", "ssh"])]

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 255
        super().__init__(*args, **kwargs)


class MultipleChoiceField(models.CharField):
    """
    Field that can take a set of string values and store them in a `CharField` using
    a delimiter. This needs to be compatible with DRF's multiple choice field.
    """

    def clean_choices(self, values):
        for value in values:
            if not value:
                continue

            exists = False
            for choice, _ in self.choices:
                if choice == value:
                    exists = True
                    break

            if not exists and not isinstance(value, list):
                raise ValidationError(f"Invalid value: {value}")

    def validate(self, value, model_instance):
        if not self.editable:
            # Skip validation for non-editable fields.
            return

        self.clean_choices(value)

        if value is None and not self.null:
            raise ValidationError(self.error_messages["null"], code="null")

        if not self.blank and value in self.empty_values:
            raise ValidationError(self.error_messages["blank"], code="blank")

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None

        if not value:
            return []

        values = value.split(",")

        self.clean_choices(values)

        return values

    def get_prep_value(self, value):
        if value is None:
            return ""

        picked = []
        for choice, _ in self.choices:
            if choice in value:
                picked.append(choice)
        return ",".join(picked)

    def to_python(self, value):
        if isinstance(value, (list, set, tuple)):
            return value

        if value is None:
            return value

        values = value.split(",")

        self.clean_choices(values)

        return values

    def formfield(self, **kwargs):
        defaults = {"form_class": MultipleChoiceField}
        defaults.update(**kwargs)
        return super().formfield(**defaults)


class Address(models.Model):
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    zipcode = models.CharField(max_length=48, blank=True)
    country = models.CharField(max_length=7, blank=True)
    suite = models.CharField(max_length=255, blank=True)
    floor = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(
        decimal_places=6, max_digits=9, blank=True, null=True
    )
    longitude = models.DecimalField(
        decimal_places=6, max_digits=9, blank=True, null=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.address1} {self.zipcode} {self.country}"


class Organization(Address):
    name = models.CharField(max_length=255, unique=True)
    name_long = models.CharField(max_length=255, blank=True)
    aka = models.CharField(max_length=255, blank=True, verbose_name="Also Known As")
    website = URLField(blank=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Campus(models.Model):
    name = models.CharField(max_length=255, unique=True)
    name_long = models.CharField(max_length=255, blank=True, null=True)
    aka = models.CharField(max_length=255, blank=True, null=True)
    website = URLField(blank=True, null=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    notes = models.TextField(blank=True)
    org = models.ForeignKey(
        to="peeringdb.Organization",
        related_name="campus_set",
        verbose_name="Organization",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name_plural = "campuses"

    def __str__(self):
        return self.name


class Facility(Address):
    name = models.CharField(max_length=255, unique=True)
    name_long = models.CharField(max_length=255, blank=True)
    aka = models.CharField(max_length=255, blank=True, verbose_name="Also Known As")
    website = URLField(blank=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    clli = models.CharField(max_length=18, blank=True)
    rencode = models.CharField(max_length=18, blank=True)
    npanxx = models.CharField(max_length=21, blank=True)
    tech_email = models.EmailField(max_length=254, blank=True)
    tech_phone = models.CharField(max_length=192, blank=True)
    sales_email = models.EmailField(max_length=254, blank=True)
    sales_phone = models.CharField(max_length=192, blank=True)
    property = models.CharField(
        max_length=27, null=True, blank=True, choices=Property.choices
    )
    diverse_serving_substations = models.BooleanField(null=True, blank=True)
    available_voltage_services = MultipleChoiceField(
        max_length=255, null=True, blank=True, choices=AvailableVoltage.choices
    )
    notes = models.TextField(blank=True)
    region_continent = models.CharField(
        max_length=255,
        choices=Region.choices,
        blank=True,
        null=True,
        verbose_name="Continental Region",
    )
    status_dashboard = URLField(null=True, blank=True)
    org = models.ForeignKey(
        to="peeringdb.Organization",
        related_name="fac_set",
        verbose_name="Organization",
        on_delete=models.CASCADE,
    )
    campus = models.ForeignKey(
        to="peeringdb.Campus",
        related_name="fac_set",
        verbose_name="Campus",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name_plural = "facilities"

    def __str__(self):
        return self.name


class Carrier(models.Model):
    name = models.CharField("Name", max_length=255, unique=True)
    aka = models.CharField("Also Known As", max_length=255, blank=True)
    name_long = models.CharField("Long Name", max_length=255, blank=True)
    website = URLField("Website", blank=True, null=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    notes = models.TextField("Notes", blank=True)
    org = models.ForeignKey(
        to="peeringdb.Organization",
        related_name="carrier_set",
        verbose_name="Organization",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class CarrierFacility(models.Model):
    carrier = models.ForeignKey(
        to="peeringdb.Carrier",
        related_name="carrierfac_set",
        verbose_name="Carrier",
        on_delete=models.CASCADE,
    )
    fac = models.ForeignKey(
        to="peeringdb.Facility",
        default=0,
        related_name="carrierfac_set",
        verbose_name="Facility",
        on_delete=models.CASCADE,
    )
    campus = models.ForeignKey(
        to="peeringdb.Campus",
        related_name="carrierfac_set",
        verbose_name="Campus",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("carrier", "fac")

    def __str__(self):
        return f"{self.carrier} @ {self.fac}"


class Network(models.Model):
    asn = ASNField(unique=True, verbose_name="ASN")
    name = models.CharField(max_length=255, unique=True)
    name_long = models.CharField(max_length=255, blank=True)
    aka = models.CharField(max_length=255, blank=True, verbose_name="Also Known As")
    irr_as_set = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="IRR AS-SET/ROUTE-SET",
        help_text="Reference to an AS-SET or ROUTE-SET in Internet Routing Registry (IRR)",
    )
    website = URLField(blank=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    looking_glass = URLField(blank=True)
    route_server = URLField(blank=True)
    notes = models.TextField(blank=True)
    notes_private = models.TextField(blank=True)
    info_traffic = models.CharField(max_length=39, blank=True, choices=Traffic.choices)
    info_ratio = models.CharField(
        max_length=45, blank=True, choices=Ratio.choices, default=Ratio.NOT_DISCLOSED
    )
    info_scope = models.CharField(
        max_length=39, blank=True, choices=Scope.choices, default=Scope.NOT_DISCLOSED
    )
    info_types = MultipleChoiceField(
        max_length=255, null=True, blank=True, choices=NetTypeMultiChoice.choices
    )
    info_type = models.CharField(
        max_length=60,
        blank=True,
        choices=NetType.choices,
        default=NetType.NOT_DISCLOSED,
    )
    info_prefixes4 = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Recommended maximum number of IPv4 routes/prefixes to be configured on peering sessions for this ASN",
    )
    info_prefixes6 = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Recommended maximum number of IPv6 routes/prefixes to be configured on peering sessions for this ASN",
    )
    info_unicast = models.BooleanField(default=False)
    info_multicast = models.BooleanField(default=False)
    info_ipv6 = models.BooleanField(default=False)
    info_never_via_route_servers = models.BooleanField(
        default=False,
        help_text="Indicates if this network will announce its routes via route servers or not",
    )
    policy_url = URLField(blank=True)
    policy_general = models.CharField(
        max_length=72, blank=True, choices=GeneralPolicy.choices
    )
    policy_locations = models.CharField(
        max_length=72, blank=True, choices=LocationsPolicy.choices
    )
    policy_ratio = models.BooleanField(default=False)
    policy_contracts = models.CharField(
        max_length=36, blank=True, choices=ContractsPolicy.choices
    )
    status_dashboard = URLField(null=True, blank=True)
    rir_status = models.CharField(blank=True, null=True, max_length=255)
    rir_status_updated = models.DateTimeField(blank=True, null=True)
    org = models.ForeignKey(
        to="peeringdb.Organization",
        related_name="net_set",
        verbose_name="Organization",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"AS{self.asn} - {self.name}"

    def render_email(self, email, network):
        """
        Renders an e-mail from a template.
        """
        return email.render({"autonomous_systems": [network, self]})


class InternetExchange(models.Model):
    name = models.CharField(max_length=64, unique=True)
    name_long = models.CharField(max_length=255, blank=True)
    aka = models.CharField(max_length=255, blank=True, verbose_name="Also Known As")
    city = models.CharField(max_length=192)
    country = models.CharField(max_length=7, blank=True)
    notes = models.TextField(blank=True)
    region_continent = models.CharField(max_length=255, choices=Region.choices)
    media = models.CharField(max_length=128, choices=Media.choices)
    proto_unicast = models.BooleanField(default=False)
    proto_multicast = models.BooleanField(default=False)
    proto_ipv6 = models.BooleanField(default=False)
    website = URLField(blank=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    url_stats = URLField(blank=True)
    tech_email = models.EmailField(max_length=254, blank=True)
    tech_phone = models.CharField(max_length=192, blank=True)
    policy_email = models.EmailField(max_length=254, blank=True)
    policy_phone = models.CharField(max_length=192, blank=True)
    sales_email = models.EmailField(max_length=254, blank=True)
    sales_phone = models.CharField(max_length=192, blank=True)
    ixf_net_count = models.IntegerField(default=0)
    ixf_last_import = models.DateTimeField(null=True, blank=True)
    service_level = models.CharField(
        max_length=60,
        blank=True,
        choices=ServiceLevels.choices,
        default=ServiceLevels.NOT_DISCLOSED,
    )
    terms = models.CharField(
        max_length=60, blank=True, choices=Terms.choices, default=Terms.NOT_DISCLOSED
    )
    status_dashboard = URLField(null=True, blank=True)
    org = models.ForeignKey(
        to="peeringdb.Organization",
        related_name="ix_set",
        verbose_name="Organization",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Internet Exchange"
        verbose_name_plural = "Internet Exchanges"

    def __str__(self):
        return self.name

    @property
    def fac_set(self):
        return [ixfac.fac for ixfac in self.ixfac_set]


class InternetExchangeFacility(models.Model):
    ix = models.ForeignKey(
        to="peeringdb.InternetExchange",
        related_name="ixfac_set",
        verbose_name="Internet Exchange",
        on_delete=models.CASCADE,
    )
    fac = models.ForeignKey(
        to="peeringdb.Facility",
        default=0,
        related_name="ixfac_set",
        verbose_name="Facility",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("ix", "fac")
        verbose_name = "Internet Exchange facility"
        verbose_name_plural = "Internet Exchange facilities"


class IXLan(models.Model):
    name = models.CharField(max_length=255, blank=True)
    descr = models.TextField(blank=True)
    mtu = models.PositiveIntegerField(null=True, blank=True, choices=MTU.choices)
    vlan = models.PositiveIntegerField(null=True, blank=True)
    dot1q_support = models.BooleanField(default=False)
    rs_asn = ASNField(
        verbose_name="Route Server ASN",
        allow_zero=True,
        null=True,
        blank=True,
        default=0,
    )
    arp_sponge = MACAddressField(
        verbose_name="ARP sponging MAC", null=True, unique=True, blank=True
    )
    ixf_ixp_member_list_url = models.URLField(
        verbose_name="IX-F Member Export URL", null=True, blank=True
    )
    ixf_ixp_member_list_url_visible = models.CharField(
        verbose_name="IX-F Member Export URL Visibility",
        max_length=64,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    ix = models.ForeignKey(
        to="peeringdb.InternetExchange",
        default=0,
        related_name="ixlan_set",
        verbose_name="Internet Exchange",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Internet Exchange LAN"
        verbose_name_plural = "Internet Exchange LANs"


class IXLanPrefix(models.Model):
    notes = models.CharField(max_length=255, blank=True)
    protocol = models.CharField(max_length=64, choices=Protocol.choices)
    prefix = CidrAddressField(unique=True)
    in_dfz = models.BooleanField(default=False)
    ixlan = models.ForeignKey(
        to="peeringdb.IXLan",
        default=0,
        related_name="ixpfx_set",
        verbose_name="Internet Exchange LAN",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Internet Exchange LAN prefix"
        verbose_name_plural = "Internet Exchange LAN prefixes"


class NetworkContact(models.Model):
    role = models.CharField(max_length=27, choices=POCRole.choices)
    visible = models.CharField(
        max_length=64, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    name = models.CharField(max_length=254, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    url = URLField(blank=True)
    net = models.ForeignKey(
        to="peeringdb.Network",
        default=0,
        related_name="poc_set",
        verbose_name="Network",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        if not self.email:
            return self.name
        return f"{self.name} <{self.email}>"


class NetworkFacility(models.Model):
    local_asn = ASNField(verbose_name="Local ASN", null=True, blank=True)
    avail_sonet = models.BooleanField(default=False)
    avail_ethernet = models.BooleanField(default=False)
    avail_atm = models.BooleanField(default=False)
    net = models.ForeignKey(
        to="peeringdb.Network",
        default=0,
        related_name="netfac_set",
        verbose_name="Network",
        on_delete=models.CASCADE,
    )
    fac = models.ForeignKey(
        to="peeringdb.Facility",
        default=0,
        related_name="netfac_set",
        verbose_name="Facility",
        on_delete=models.CASCADE,
    )

    ignored_fields = ["city", "country", "name"]

    class Meta:
        unique_together = ("net", "fac", "local_asn")
        verbose_name = "Network Facility"
        verbose_name_plural = "Network Facilities"


class NetworkIXLan(models.Model):
    asn = ASNField(verbose_name="ASN")
    ipaddr4 = InetAddressField(
        verbose_name="IPv4",
        validators=[AddressFamilyValidator(4)],
        blank=True,
        null=True,
    )
    ipaddr6 = InetAddressField(
        verbose_name="IPv6",
        validators=[AddressFamilyValidator(6)],
        blank=True,
        null=True,
    )
    is_rs_peer = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)
    speed = models.PositiveIntegerField()
    operational = models.BooleanField(default=True)
    net = models.ForeignKey(
        to="peeringdb.Network",
        default=0,
        related_name="netixlan_set",
        verbose_name="Network",
        on_delete=models.CASCADE,
    )
    ixlan = models.ForeignKey(
        to="peeringdb.IXLan",
        default=0,
        related_name="netixlan_set",
        verbose_name="Internet Exchange LAN",
        on_delete=models.CASCADE,
    )

    ignored_fields = ["ix_id", "name"]

    class Meta:
        verbose_name = "Public Peering Exchange Point"
        verbose_name_plural = "Public Peering Exchange Points"

    @property
    def cidr4(self):
        try:
            return self.cidr(address_family=4)
        except ValueError:
            return None

    @property
    def cidr6(self):
        try:
            return self.cidr(address_family=6)
        except ValueError:
            return None

    def get_ixlan_prefix(self, address_family=0):
        """
        Returns matching `CidrAddressField` containing this `NetworkIXLan`'s IP
        addresses. When `address_family` is set to `4` or `6` only the prefix also
        matching the address family will be returned.
        """
        prefixes = IXLanPrefix.objects.filter(ixlan=self.ixlan)
        if address_family in (4, 6):
            prefixes = prefixes.filter(prefix__family=address_family)

        r = []
        if address_family != 6:
            for p in prefixes:
                if self.ipaddr4 in p.prefix:
                    r.append(p.prefix)
                    break
        if address_family != 4:
            for p in prefixes:
                if self.ipaddr6 in p.prefix:
                    r.append(p.prefix)
                    break

        return r

    def cidr(self, address_family=4):
        """
        Returns a Python IP interface object with the IP address and prefix length
        set.
        """
        if address_family not in (4, 6):
            raise ValueError("Address family must be 4 or 6")
        if address_family == 4 and not self.ipaddr4:
            raise ValueError("IPv4 address is not set")
        if address_family == 6 and not self.ipaddr6:
            raise ValueError("IPv6 address is not set")

        address = self.ipaddr4 if address_family == 4 else self.ipaddr6
        for prefix in self.get_ixlan_prefix(address_family=address_family):
            if address in prefix:
                return ipaddress.ip_interface(f"{address.ip}/{prefix.prefixlen}")

        raise ValueError("No CIDR formatted IP address found")


class Synchronisation(models.Model):
    time = models.DateTimeField()
    created = models.PositiveIntegerField()
    updated = models.PositiveIntegerField()
    deleted = models.PositiveIntegerField()

    class Meta:
        ordering = ["-time"]

    def __str__(self):
        return f"Synchronised {(self.created + self.deleted + self.updated)} objects at {self.time}"
