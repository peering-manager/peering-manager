from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from django.db.models import ManyToManyField, Model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import BindingDict

from peering_manager.registry import MODEL_FEATURES_KEY, registry

from .fields import (
    PeeringManagerAPIHyperlinkedIdentityField,
    PeeringManagerURLHyperlinkedIdentityField,
)

if TYPE_CHECKING:
    from django.db.models import Model


__all__ = ("BaseModelSerializer", "ValidatedModelSerializer")


class BaseModelSerializer(serializers.ModelSerializer):
    url = PeeringManagerAPIHyperlinkedIdentityField()
    display_url = PeeringManagerURLHyperlinkedIdentityField()
    display = serializers.SerializerMethodField(read_only=True)
    config_context = serializers.SerializerMethodField(read_only=True, allow_null=True)

    def __init__(
        self,
        *args: Any,
        nested: bool = False,
        fields: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self.nested = nested
        self._requested_fields = fields

        super().__init__(*args, **kwargs)

    @cached_property
    def fields(self) -> BindingDict:
        """
        Override the fields property to check for requested fields. If defined,
        return only the applicable fields.
        """
        if not self._requested_fields:
            return super().fields

        fields = BindingDict(self)
        for key, value in self.get_fields().items():
            if key in self._requested_fields:
                fields[key] = value
        return fields

    def get_display(self, obj: Model) -> str:
        return str(obj)

    @extend_schema_field(serializers.JSONField(allow_null=True))
    def get_config_context(self, obj: type[Model]):
        if obj._meta.model_name not in registry[MODEL_FEATURES_KEY][
            "config-contexts"
        ].get(obj._meta.app_label, []):
            return None
        return obj.get_config_context()


class ValidatedModelSerializer(BaseModelSerializer):
    """
    Extends the built-in `ModelSerializer` to enforce calling `full_clean()` on a copy
    of the associated instance during validation.

    DRF does not do this by default:
    https://github.com/encode/django-rest-framework/issues/3144
    """

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
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
