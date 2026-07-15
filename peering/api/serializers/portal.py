from __future__ import annotations

from rest_framework import serializers

from peering_manager.api.fields import IPInterfaceField

from ...constants import (
    ASN_MAX,
    ASN_MIN,
    FACILITY_LOCATION_PREFIX,
    IX_LOCATION_PREFIX,
    format_facility_location,
    format_ix_location,
)
from ...enums import PeeringRequestType

__all__ = (
    "PortalAffiliatedSerializer",
    "PortalContactSerializer",
    "PortalLocationSerializer",
    "PortalLocationsResponseSerializer",
    "PortalNetworkSerializer",
    "PortalRequestListSerializer",
    "PortalRequestStatusSerializer",
    "PortalRequestedSessionStatusSerializer",
    "PortalSessionEntrySerializer",
    "PortalSessionInfoSerializer",
    "PortalSessionSubmitResponseSerializer",
    "PortalSessionSubmitSerializer",
)


class PortalAffiliatedSerializer(serializers.Serializer):
    asn = serializers.IntegerField()
    name = serializers.CharField()


class PortalContactSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()


class PortalNetworkSerializer(serializers.Serializer):
    asn = serializers.IntegerField()
    name = serializers.CharField()
    name_long = serializers.CharField()
    info_prefixes4 = serializers.IntegerField(allow_null=True)
    info_prefixes6 = serializers.IntegerField(allow_null=True)
    irr_as_set = serializers.CharField()
    policy_general = serializers.CharField()
    contacts = PortalContactSerializer(many=True)


class PortalSessionInfoSerializer(serializers.Serializer):
    local_ip = IPInterfaceField()
    peer_ip = IPInterfaceField()
    address_family = serializers.IntegerField()
    existing = serializers.BooleanField()


class PortalLocationSerializer(serializers.Serializer):
    location = serializers.CharField(
        help_text=f"{IX_LOCATION_PREFIX}$IX_ID for public peering, {FACILITY_LOCATION_PREFIX}$FACILITY_ID for private"
    )
    name = serializers.CharField()
    peering_type = serializers.CharField()
    sessions = PortalSessionInfoSerializer(many=True)


class PortalLocationsResponseSerializer(serializers.Serializer):
    locations = PortalLocationSerializer(many=True)
    peer_asn = serializers.IntegerField()


class PortalSessionEntrySerializer(serializers.Serializer):
    local_ip = IPInterfaceField(required=True)
    location = serializers.CharField(required=True)
    peer_ip = IPInterfaceField(required=True)
    session_secret = serializers.CharField(required=False, allow_blank=True, default="")


class PortalSessionSubmitSerializer(serializers.Serializer):
    local_asn = serializers.IntegerField(required=True, min_value=ASN_MIN, max_value=ASN_MAX)
    peer_type = serializers.ChoiceField(choices=PeeringRequestType.CHOICES, required=True)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    sessions = PortalSessionEntrySerializer(many=True, min_length=1)


class PortalSessionSubmitResponseSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    status = serializers.CharField()
    sessions_count = serializers.IntegerField()


class PortalRequestedSessionStatusSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(source="id")
    local_ip = IPInterfaceField(source="ip_address")
    peer_ip = IPInterfaceField(source="peer_ip_address", allow_null=True)
    location = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    status = serializers.CharField()
    rejection_comment = serializers.CharField()

    def get_location(self, obj) -> str:
        if obj.ixp_connection and obj.ixp_connection.internet_exchange_point:
            ix = obj.ixp_connection.internet_exchange_point
            if ix.peeringdb_ixlan:
                return format_ix_location(ix.peeringdb_ixlan.pk)
        if obj.peeringdb_facility:
            return format_facility_location(obj.peeringdb_facility.pk)
        return ""

    def get_location_name(self, obj) -> str:
        if obj.ixp_connection and obj.ixp_connection.internet_exchange_point:
            return obj.ixp_connection.internet_exchange_point.name
        if obj.peeringdb_facility:
            return obj.peeringdb_facility.name
        return ""


class PortalRequestStatusSerializer(serializers.Serializer):
    request_id = serializers.UUIDField(source="tracking_id")
    status = serializers.CharField()
    peer_type = serializers.CharField(source="request_type")
    local_asn = serializers.IntegerField(source="requesting_asn")
    peer_asn = serializers.SerializerMethodField()
    decision_comment = serializers.CharField()
    sessions = PortalRequestedSessionStatusSerializer(source="requested_sessions", many=True)
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()

    def get_peer_asn(self, obj) -> int:
        return obj.local_autonomous_system.asn


class PortalRequestListSerializer(serializers.Serializer):
    requests = PortalRequestStatusSerializer(many=True)
