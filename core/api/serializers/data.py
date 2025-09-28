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
    "DataSourceSerializer",
    "NestedDataFileSerializer",
    "NestedDataSourceSerializer",
)


class DataSourceSerializer(PeeringManagerModelSerializer):
    type = ChoiceField(choices=get_data_backend_choices())
    status = ChoiceField(choices=DataSourceStatus, read_only=True)
    file_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DataSource
        fields = [
            "id",
            "url",
            "display_url",
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
    class Meta:
        model = DataSource
        fields = ["id", "url", "display_url", "display", "name"]


class DataFileSerializer(PeeringManagerModelSerializer):
    source = NestedDataSourceSerializer(read_only=True)

    class Meta:
        model = DataFile
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "source",
            "path",
            "updated",
            "size",
            "hash",
        ]


class NestedDataFileSerializer(WritableNestedSerializer):
    class Meta:
        model = DataFile
        fields = ["id", "url", "display_url", "display", "path"]
