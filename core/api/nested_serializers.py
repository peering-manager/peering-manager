from rest_framework import serializers

from peering_manager.api.fields import ChoiceField
from peering_manager.api.serializers import WritableNestedSerializer
from users.api.nested_serializers import NestedUserSerializer

from ..enums import *
from ..models import *

__all__ = (
    "NestedDataFileSerializer",
    "NestedDataSourceSerializer",
    "NestedJobSerializer",
)


class NestedDataFileSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:datafile-detail")

    class Meta:
        model = DataFile
        fields = ["id", "url", "display", "path"]


class NestedDataSourceSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:datasource-detail")

    class Meta:
        model = DataSource
        fields = ["id", "url", "display", "name"]


class NestedJobSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:job-detail")
    status = ChoiceField(choices=JobStatus)
    user = NestedUserSerializer(read_only=True)

    class Meta:
        model = Job
        fields = ["url", "created", "completed", "user", "status"]
