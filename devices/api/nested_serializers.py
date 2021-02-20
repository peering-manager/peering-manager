from rest_framework import serializers

from devices.models import Platform


class PlatformNestedSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="devices-api:platform-detail")

    class Meta:
        model = Platform
        fields = ["id", "url", "name", "slug"]
