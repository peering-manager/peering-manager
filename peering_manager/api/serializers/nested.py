from django.core.exceptions import (
    FieldError,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
)
from rest_framework.exceptions import ValidationError

from extras.models import Tag
from utils.functions import dict_to_filter_params

from .base import BaseModelSerializer

__all__ = ("NestedTagSerializer", "WritableNestedSerializer")


class WritableNestedSerializer(BaseModelSerializer):
    """
    Represents an object related through a `ForeignKey` field.

    On write, it accepts a primary key (PK) value or a dictionary of attributes which
    can be used to uniquely identify the related object. This class should be
    subclassed to return a full representation of the related object on read.
    """

    def to_internal_value(self, data):
        if data is None:
            return None

        # Dictionary of related object attributes
        if isinstance(data, dict):
            params = dict_to_filter_params(data)
            queryset = self.Meta.model.objects
            try:
                return queryset.get(**params)
            except ObjectDoesNotExist as e1:
                raise ValidationError(
                    f"Related object not found using the provided attributes: {params}"
                ) from e1
            except MultipleObjectsReturned as e2:
                raise ValidationError(
                    f"Multiple objects match the provided attributes: {params}"
                ) from e2
            except FieldError as e3:
                raise ValidationError(e3) from e3

        # Integer PK of related object
        try:
            # Cast as integer in case a PK was mistakenly sent as a string
            pk = int(data)
        except (TypeError, ValueError) as e:
            raise ValidationError(
                f"Related objects must be referenced by numeric ID or by dictionary of attributes. Received an unrecognized value: {data}"
            ) from e

        # Look up object by PK
        try:
            return self.Meta.model.objects.get(pk=pk)
        except ObjectDoesNotExist as e:
            raise ValidationError(
                f"Related object not found using the provided numeric ID: {pk}"
            ) from e


# Declared here for use by PeeringManagerModelSerializer, but should be imported from
# extras.api.nested_serializers
class NestedTagSerializer(WritableNestedSerializer):
    class Meta:
        model = Tag
        fields = ["id", "url", "display_url", "display", "name", "slug", "color"]
