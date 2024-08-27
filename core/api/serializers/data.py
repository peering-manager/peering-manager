from rest_framework import serializers

from peering_manager.api.fields import ChoiceField
from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    WritableNestedSerializer,
)

from ...enums import *
from ...models import *
from ...utils import get_data_backend_choices

__all__ = (
    "DataFileSerializer",
    "NestedDataFileSerializer",
    "DataSourceSerializer",
    "NestedDataSourceSerializer",
)


class DataSourceSerializer(PeeringManagerModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:datasource-detail")
    type = ChoiceField(choices=get_data_backend_choices())
    status = ChoiceField(choices=DataSourceStatus, read_only=True)
    file_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DataSource
        fields = [
            "id",
            "url",
            "display",
            "name",
            "type",
            "source_url",
            "enabled",
            "status",
            "description",
            "comments",
            "parameters",
            "ignore_rules",
            "created",
            "updated",
            "file_count",
        ]


class NestedDataSourceSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:datasource-detail")

    class Meta:
        model = DataSource
        fields = ["id", "url", "display", "name"]


class DataFileSerializer(PeeringManagerModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:datafile-detail")
    source = NestedDataSourceSerializer(read_only=True)

    class Meta:
        model = DataFile
        fields = ["id", "url", "display", "source", "path", "updated", "size", "hash"]


class NestedDataFileSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:datafile-detail")

    class Meta:
        model = DataFile
        fields = ["id", "url", "display", "path"]
