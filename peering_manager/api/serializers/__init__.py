from rest_framework import serializers

from .base import *
from .features import *
from .generic import *
from .nested import *


class PeeringManagerModelSerializer(TaggableModelSerializer, ValidatedModelSerializer):
    """
    Adds support for tags.
    """

    pass


class BulkOperationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
