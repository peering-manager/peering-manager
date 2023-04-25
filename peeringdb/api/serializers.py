from rest_framework import serializers

from peering_manager.api.fields import ChoiceField
from peeringdb.enums import Visibility
from peeringdb.models import (
    Facility,
    InternetExchange,
    InternetExchangeFacility,
    IXLan,
    IXLanPrefix,
    Network,
    NetworkContact,
    NetworkFacility,
    NetworkIXLan,
    Organization,
    Synchronisation,
)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "address1",
            "address2",
            "city",
            "state",
            "zipcode",
            "country",
            "latitude",
            "longitude",
            "suite",
            "floor",
            "name",
            "name_long",
            "aka",
            "website",
            "notes",
        ]


class InternetExchangeSerializer(serializers.ModelSerializer):
    org = OrganizationSerializer()

    class Meta:
        model = InternetExchange
        fields = [
            "name",
            "name_long",
            "aka",
            "city",
            "country",
            "notes",
            "region_continent",
            "media",
            "proto_unicast",
            "proto_multicast",
            "proto_ipv6",
            "website",
            "url_stats",
            "tech_email",
            "tech_phone",
            "policy_email",
            "policy_phone",
            "sales_email",
            "sales_phone",
            "ixf_net_count",
            "ixf_last_import",
            "service_level",
            "terms",
            "org",
        ]
        # Avoid conflig with `InternetExchange` in `peering` module
        ref_name = "PDBInternetExchange"


class FacilitySerializer(serializers.ModelSerializer):
    org = OrganizationSerializer()

    class Meta:
        model = Facility
        fields = [
            "address1",
            "address2",
            "city",
            "state",
            "zipcode",
            "country",
            "latitude",
            "longitude",
            "suite",
            "floor",
            "name",
            "name_long",
            "aka",
            "website",
            "clli",
            "rencode",
            "npanxx",
            "tech_email",
            "tech_phone",
            "sales_email",
            "sales_phone",
            "property",
            "diverse_serving_substations",
            "available_voltage_services",
            "notes",
            "org",
        ]


class InternetExchangeFacilitySerializer(serializers.ModelSerializer):
    ix = InternetExchangeSerializer()
    fac = FacilitySerializer()

    class Meta:
        model = InternetExchangeFacility
        fields = ["ix", "fac"]


class IXLanSerializer(serializers.ModelSerializer):
    ix = InternetExchangeSerializer()

    class Meta:
        model = IXLan
        fields = [
            "name",
            "descr",
            "mtu",
            "vlan",
            "dot1q_support",
            "rs_asn",
            "arp_sponge",
            "ixf_ixp_member_list_url",
            "ixf_ixp_member_list_url_visible",
            "ix",
        ]


class IXLanPrefixSerializer(serializers.ModelSerializer):
    ixlan = IXLanSerializer()

    class Meta:
        model = IXLanPrefix
        fields = ["notes", "protocol", "prefix", "in_dfz", "ixlan"]


class NetworkSerializer(serializers.ModelSerializer):
    org = OrganizationSerializer()

    class Meta:
        model = Network
        fields = [
            "asn",
            "name",
            "name_long",
            "aka",
            "irr_as_set",
            "website",
            "looking_glass",
            "route_server",
            "notes",
            "notes_private",
            "info_traffic",
            "info_ratio",
            "info_scope",
            "info_type",
            "info_prefixes4",
            "info_prefixes6",
            "info_unicast",
            "info_multicast",
            "info_ipv6",
            "info_never_via_route_servers",
            "policy_url",
            "policy_general",
            "policy_locations",
            "policy_ratio",
            "policy_contracts",
            "org",
        ]


class NetworkContactSerializer(serializers.ModelSerializer):
    visible = ChoiceField(choices=Visibility.choices)
    net = NetworkSerializer()

    class Meta:
        model = NetworkContact
        fields = ["role", "visible", "name", "phone", "email", "url", "net"]


class NetworkFacilitySerializer(serializers.ModelSerializer):
    net = NetworkSerializer()
    fac = FacilitySerializer()

    class Meta:
        model = NetworkFacility
        fields = [
            "local_asn",
            "avail_sonet",
            "avail_ethernet",
            "avail_atm",
            "net",
            "fac",
        ]


class NetworkIXLanSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkIXLan
        fields = [
            "asn",
            "ipaddr4",
            "ipaddr6",
            "is_rs_peer",
            "notes",
            "speed",
            "operational",
            "net",
            "ixlan",
        ]


class SynchronisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Synchronisation
        fields = ["id", "time", "created", "updated", "deleted"]
