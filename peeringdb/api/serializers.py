from rest_framework import serializers

from peeringdb.models import Synchronization


class SynchronizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Synchronization
        fields = ["time", "added", "updated", "deleted"]
