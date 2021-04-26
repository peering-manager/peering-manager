import logging

from django.core.validators import URLValidator
from django.db import models
from netfields import CidrAddressField, InetAddressField, MACAddressField

from peering.fields import ASNField
from utils.validators import AddressFamilyValidator

from .enums import (
    ContractsPolicy,
    GeneralPolicy,
    LocationsPolicy,
    Media,
    NetType,
    POCRole,
    Protocol,
    Ratio,
    Region,
    Scope,
    Traffic,
    Visibility,
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
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Facility(Address):
    name = models.CharField(max_length=255, unique=True)
    name_long = models.CharField(max_length=255, blank=True)
    aka = models.CharField(max_length=255, blank=True, verbose_name="Also Known As")
    website = URLField(blank=True)
    clli = models.CharField(max_length=18, blank=True)
    rencode = models.CharField(max_length=18, blank=True)
    npanxx = models.CharField(max_length=21, blank=True)
    tech_email = models.EmailField(max_length=254, blank=True)
    tech_phone = models.CharField(max_length=192, blank=True)
    sales_email = models.EmailField(max_length=254, blank=True)
    sales_phone = models.CharField(max_length=192, blank=True)
    notes = models.TextField(blank=True)
    org = models.ForeignKey(
        Organization,
        related_name="fac_set",
        verbose_name="Organization",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name_plural = "facilities"

    def __str__(self):
        return self.name


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
    looking_glass = URLField(blank=True)
    route_server = URLField(blank=True)
    notes = models.TextField(blank=True)
    notes_private = models.TextField(blank=True)
    info_traffic = models.CharField(max_length=39, blank=True, choices=Traffic.choices)
    info_ratio = models.CharField(
        max_length=45,
        blank=True,
        choices=Ratio.choices,
        default=Ratio.NOT_DISCLOSED,
    )
    info_scope = models.CharField(
        max_length=39,
        blank=True,
        choices=Scope.choices,
        default=Scope.NOT_DISCLOSED,
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
        max_length=72,
        blank=True,
        choices=LocationsPolicy.choices,
    )
    policy_ratio = models.BooleanField(default=False)
    policy_contracts = models.CharField(
        max_length=36,
        blank=True,
        choices=ContractsPolicy.choices,
    )
    org = models.ForeignKey(
        Organization,
        related_name="net_set",
        verbose_name="Organization",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


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
    url_stats = URLField(blank=True)
    tech_email = models.EmailField(max_length=254, blank=True)
    tech_phone = models.CharField(max_length=192, blank=True)
    policy_email = models.EmailField(max_length=254, blank=True)
    policy_phone = models.CharField(max_length=192, blank=True)
    ixf_net_count = models.IntegerField(default=0)
    ixf_last_import = models.DateTimeField(null=True, blank=True)
    org = models.ForeignKey(
        Organization,
        related_name="ix_set",
        verbose_name="Organization",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Internet Exchange"
        verbose_name_plural = "Internet Exchanges"

    @property
    def fac_set(self):
        return [ixfac.fac for ixfac in self.ixfac_set]

    def __str__(self):
        return self.name


class InternetExchangeFacility(models.Model):
    ix = models.ForeignKey(
        InternetExchange,
        related_name="ixfac_set",
        verbose_name="Internet Exchange",
        on_delete=models.CASCADE,
    )
    fac = models.ForeignKey(
        Facility,
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
    mtu = models.PositiveIntegerField(null=True, blank=True)
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
        InternetExchange,
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
        IXLan,
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
        Network,
        default=0,
        related_name="poc_set",
        verbose_name="Network",
        on_delete=models.CASCADE,
    )


class NetworkFacility(models.Model):
    local_asn = ASNField(verbose_name="Local ASN", null=True, blank=True)
    avail_sonet = models.BooleanField(default=False)
    avail_ethernet = models.BooleanField(default=False)
    avail_atm = models.BooleanField(default=False)
    net = models.ForeignKey(
        Network,
        default=0,
        related_name="netfac_set",
        verbose_name="Network",
        on_delete=models.CASCADE,
    )
    fac = models.ForeignKey(
        Facility,
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
        Network,
        default=0,
        related_name="netixlan_set",
        verbose_name="Network",
        on_delete=models.CASCADE,
    )
    ixlan = models.ForeignKey(
        IXLan,
        default=0,
        related_name="netixlan_set",
        verbose_name="Internet Exchange LAN",
        on_delete=models.CASCADE,
    )

    ignored_fields = ["ix_id", "name"]

    class Meta:
        verbose_name = "Public Peering Exchange Point"
        verbose_name_plural = "Public Peering Exchange Points"


class Synchronization(models.Model):
    time = models.DateTimeField()
    created = models.PositiveIntegerField()
    updated = models.PositiveIntegerField()
    deleted = models.PositiveIntegerField()

    class Meta:
        ordering = ["-time"]

    def __str__(self):
        return f"Synced {(self.created + self.deleted + self.updated)} objects at {self.time}"
