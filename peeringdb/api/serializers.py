from rest_framework import serializers

from peeringdb.models import Contact, Network, NetworkIXLAN, PeerRecord, Synchronization


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "role", "visible", "name", "phone", "email", "url", "net_id"]


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
    network = NetworkSerializer(read_only=True)
    network_ixlan = NetworkIXLANSerializer(read_only=True)

    class Meta:
        model = PeerRecord
        fields = ["id", "network", "network_ixlan", "visible"]


class SynchronizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Synchronization
        fields = ["id", "time", "added", "updated", "deleted"]
