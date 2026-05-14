from __future__ import annotations

from rest_framework import serializers

from peering_manager.api.fields import IPInterfaceField

from ...enums import PeeringRequestType
from ..constants import IX_LOCATION_PREFIX

__all__ = (
    "PortalContactSerializer",
    "PortalFacilitySerializer",
    "PortalLocationSerializer",
    "PortalNetworkSerializer",
    "PortalRequestStatusSerializer",
    "PortalRequestedSessionStatusSerializer",
    "PortalSessionEntrySerializer",
    "PortalSessionInfoSerializer",
    "PortalSessionSubmitResponseSerializer",
    "PortalSessionSubmitSerializer",
)


class PortalContactSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.CharField()


class PortalNetworkSerializer(serializers.Serializer):
    asn = serializers.IntegerField()
    name = serializers.CharField()
    name_long = serializers.CharField()
    info_prefixes4 = serializers.IntegerField()
    info_prefixes6 = serializers.IntegerField()
    irr_as_set = serializers.CharField()
    policy_general = serializers.CharField()
    contacts = PortalContactSerializer(many=True)


class PortalSessionInfoSerializer(serializers.Serializer):
    local_ip = IPInterfaceField()
    peer_ip = IPInterfaceField()
    address_family = serializers.IntegerField()
    existing = serializers.BooleanField()


class PortalSessionEntrySerializer(serializers.Serializer):
    local_ip = IPInterfaceField(required=True)
    location = serializers.CharField(required=False, allow_blank=True)
    peer_ip = IPInterfaceField(required=False, allow_blank=True, default="")
    session_secret = serializers.CharField(required=False, allow_blank=True, default="")


class PortalSessionSubmitSerializer(serializers.Serializer):
    local_asn = serializers.IntegerField(required=True)
    peer_type = serializers.ChoiceField(
        choices=PeeringRequestType.CHOICES, required=True
    )
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    sessions = PortalSessionEntrySerializer(many=True, min_length=1)


class PortalSessionSubmitResponseSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    status = serializers.CharField()
    sessions_count = serializers.IntegerField()


class PortalRequestedSessionStatusSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(source="id")
    local_ip = IPInterfaceField(source="ip_address")
    peer_ip = IPInterfaceField(source="peer_ip_address", default="")
    location = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    status = serializers.CharField()
    rejection_comment = serializers.CharField()

    def get_location(self, obj) -> str:
        if obj.ixp_connection and obj.ixp_connection.internet_exchange_point:
            ix = obj.ixp_connection.internet_exchange_point
            if ix.peeringdb_ixlan:
                return f"{IX_LOCATION_PREFIX}{ix.peeringdb_ixlan.pk}"
        if obj.peeringdb_facility:
            return str(obj.peeringdb_facility.pk)
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
    sessions = PortalRequestedSessionStatusSerializer(
        source="requested_sessions", many=True
    )
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()

    def get_peer_asn(self, obj) -> int:
        return obj.local_autonomous_system.asn


class PortalLocationSerializer(serializers.Serializer):
    location = serializers.CharField(
        help_text=f"RFC format: {IX_LOCATION_PREFIX}$IX_ID"
    )
    name = serializers.CharField()
    peering_type = serializers.CharField()
    sessions = PortalSessionInfoSerializer(many=True)


class PortalFacilitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    city = serializers.CharField()
    country = serializers.CharField()
