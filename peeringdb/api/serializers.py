from rest_framework import serializers

from peeringdb.models import Network, NetworkIXLAN, PeerRecord, Synchronization


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Network
        fields = ["id", "asn", "name", "irr_as_set", "info_prefixes6", "info_prefixes4"]


class NetworkIXLANSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkIXLAN
        fields = [
            "id",
            "asn",
            "name",
            "ipaddr6",
            "ipaddr4",
            "is_rs_peer",
            "ix_id",
            "ixlan_id",
        ]


class PeerRecordSerializer(serializers.ModelSerializer):
    network = NetworkSerializer()
    network_ixlan = NetworkIXLANSerializer()

    class Meta:
        model = PeerRecord
        fields = ["id", "network", "network_ixlan"]


class SynchronizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Synchronization
        fields = ["id", "time", "added", "updated", "deleted"]
