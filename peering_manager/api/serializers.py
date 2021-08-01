from django.core.exceptions import (
    FieldError,
    MultipleObjectsReturned,
    ObjectDoesNotExist,
)
from django.db.models import ManyToManyField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from utils.functions import dict_to_filter_params
from utils.models import Tag

__all__ = [
    "BaseModelSerializer",
    "PrimaryModelSerializer",
    "ValidatedModelSerializer",
    "WritableNestedSerializer",
]


class BaseModelSerializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField(read_only=True)

    def get_display(self, instance):
        return str(instance)


class ValidatedModelSerializer(BaseModelSerializer):
    """
    Extends the built-in `ModelSerializer` to enforce calling `full_clean()` on a copy
    of the associated instance during validation.

    DRF does not do this by default; see
    https://github.com/encode/django-rest-framework/issues/3144
    """

    def validate(self, data):
        # Remove tags (if any) prior to model validation
        attrs = data.copy()
        attrs.pop("tags", None)

        # Skip ManyToManyFields
        for field in self.Meta.model._meta.get_fields():
            if isinstance(field, ManyToManyField):
                attrs.pop(field.name, None)

        # Run clean() on an instance of the model
        if self.instance is None:
            instance = self.Meta.model(**attrs)
        else:
            instance = self.instance
            for k, v in attrs.items():
                setattr(instance, k, v)
        instance.full_clean()

        return data


class WritableNestedSerializer(BaseModelSerializer):
    """
    Returns a nested representation of an object on read, but accepts only a primary
    key on write.
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
            except ObjectDoesNotExist:
                raise ValidationError(
                    f"Related object not found using the provided attributes: {params}"
                )
            except MultipleObjectsReturned:
                raise ValidationError(
                    f"Multiple objects match the provided attributes: {params}"
                )
            except FieldError as e:
                raise ValidationError(e)

        # Integer PK of related object
        if isinstance(data, int):
            pk = data
        else:
            try:
                # PK might have been mistakenly passed as a string
                pk = int(data)
            except (TypeError, ValueError):
                raise ValidationError(
                    f"Related objects must be referenced by numeric ID or by dictionary of attributes. Received an unrecognized value: {data}"
                )

        # Look up object by PK
        queryset = self.Meta.model.objects
        try:
            return queryset.get(pk=int(data))
        except ObjectDoesNotExist:
            raise ValidationError(
                f"Related object not found using the provided numeric ID: {pk}"
            )


class NestedTagSerializer(WritableNestedSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="utils-api:tag-detail")

    class Meta:
        model = Tag
        fields = ["id", "url", "display", "name", "slug", "color"]


class PrimaryModelSerializer(ValidatedModelSerializer):
    """
    Adds support for tags.
    """

    tags = NestedTagSerializer(many=True, required=False)

    def _save_tags(self, instance, tags):
        if tags:
            instance.tags.set(*[t.name for t in tags])
        else:
            instance.tags.clear()

        return instance

    def create(self, validated_data):
        tags = validated_data.pop("tags", None)
        instance = super().create(validated_data)

        if tags is not None:
            return self._save_tags(instance, tags)
        else:
            return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)

        # Cache tags on instance for change logging
        instance._tags = tags or []

        instance = super().update(instance, validated_data)

        if tags is not None:
            return self._save_tags(instance, tags)
        else:
            return instance
