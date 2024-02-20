from rest_framework import serializers

from peering_manager.api.fields import ChoiceField, ContentTypeField
from peering_manager.api.serializers import (
    BaseModelSerializer,
    PeeringManagerModelSerializer,
)
from users.api.nested_serializers import NestedUserSerializer

from ..enums import *
from ..models import *
from ..utils import get_data_backend_choices
from .nested_serializers import *

__all__ = ("DataFileSerializer", "DataSourceSerializer", "JobSerializer")


class DataFileSerializer(PeeringManagerModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:datafile-detail")
    source = NestedDataSourceSerializer(read_only=True)

    class Meta:
        model = DataFile
        fields = ["id", "url", "display", "source", "path", "updated", "size", "hash"]


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


class JobSerializer(BaseModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core-api:job-detail")
    user = NestedUserSerializer(read_only=True)
    status = ChoiceField(choices=JobStatus, read_only=True)
    object_type = ContentTypeField(read_only=True)
    output = serializers.CharField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "url",
            "display",
            "object_type",
            "object_id",
            "name",
            "status",
            "created",
            "started",
            "completed",
            "user",
            "data",
            "job_id",
            "output",
        ]
