import re

from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import (
    build_basic_type,
    build_choice_field,
    build_media_type_object,
    build_object_type,
    get_doc,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.relations import ManyRelatedField

from peering_manager.api import serializers
from peering_manager.api.fields import ChoiceField, SerializedPKRelatedField
from peering_manager.api.serializers import WritableNestedSerializer

# see peering_manager.api.routers.PeeringManagerRouter
BULK_ACTIONS = ("bulk_destroy", "bulk_partial_update", "bulk_update")
WRITABLE_ACTIONS = ("PATCH", "POST", "PUT")


class ChoiceFieldFix(OpenApiSerializerFieldExtension):
    target_class = "peering_manager.api.fields.ChoiceField"

    def map_serializer_field(self, auto_schema, direction):
        if direction == "request":
            return build_choice_field(self.target)
        if direction == "response":
            return build_object_type(
                properties={
                    "value": build_basic_type(OpenApiTypes.STR),
                    "label": build_basic_type(OpenApiTypes.STR),
                }
            )
        return None


class CidrAddressFieldFix(OpenApiSerializerFieldExtension):
    target_class = "netfields.rest_framework.CidrAddressField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)


class InetAddressFieldFix(OpenApiSerializerFieldExtension):
    target_class = "netfields.rest_framework.InetAddressField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)


class MACAddressFieldFix(OpenApiSerializerFieldExtension):
    target_class = "netfields.rest_framework.MACAddressField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)


class PeeringManagerAutoSchema(AutoSchema):
    """
    Overrides to drf_spectacular.openapi.AutoSchema to fix following issues:
      1. bulk serializers cause operation_id conflicts with non-bulk ones
      2. bulk operations should specify a list
      3. bulk operations don't have filter params
      4. bulk operations don't have pagination
      5. bulk delete should specify input
    """

    writable_serializers = {}

    @property
    def is_bulk_action(self):
        return hasattr(self.view, "action") and self.view.action in BULK_ACTIONS

    def get_operation_id(self):
        """
        bulk serializers cause operation_id conflicts with non-bulk ones
        bulk operations cause id conflicts in spectacular resulting in numerous:
        Warning: operationId "xxx" has collisions [xxx]. "resolving with numeral suffixes"
        code is modified from drf_spectacular.openapi.AutoSchema.get_operation_id
        """
        if self.is_bulk_action:
            tokenized_path = self._tokenize_path()
            # replace dashes as they can be problematic later in code generation
            tokenized_path = [t.replace("-", "_") for t in tokenized_path]

            if self.method == "GET" and self._is_list_view():
                # this shouldn't happen, but keeping it here to follow base code
                action = "list"
            else:
                # use bulk name so partial_update -> bulk_partial_update
                action = self.view.action.lower()

            if not tokenized_path:
                tokenized_path.append("root")

            if re.search(r"<drf_format_suffix\w*:\w+>", self.path_regex):
                tokenized_path.append("formatted")

            return "_".join([*tokenized_path, action])

        # if not bulk - just return normal id
        return super().get_operation_id()

    def get_request_serializer(self):
        # bulk operations should specify a list
        serializer = super().get_request_serializer()

        if self.is_bulk_action:
            return type(serializer)(many=True)

        # handle mapping for Writable serializers - adapted from dansheps original code
        # for drf-yasg
        if serializer is not None and self.method in WRITABLE_ACTIONS:
            writable_class = self.get_writable_class(serializer)
            if writable_class is not None:
                if hasattr(serializer, "child"):
                    child_serializer = self.get_writable_class(serializer.child)
                    serializer = writable_class(
                        context=serializer.context, child=child_serializer
                    )
                else:
                    serializer = writable_class(context=serializer.context)

        return serializer

    def get_response_serializers(self):
        # bulk operations should specify a list
        response_serializers = super().get_response_serializers()

        if self.is_bulk_action:
            return type(response_serializers)(many=True)

        return response_serializers

    def get_serializer_ref_name(self, serializer):
        """
        Get serializer's ref_name (or `None` for `ModelSerializer` if it is named
        'NestedSerializer')
        """
        serializer_meta = getattr(serializer, "Meta", None)
        serializer_name = type(serializer).__name__
        if hasattr(serializer_meta, "ref_name"):
            ref_name = serializer_meta.ref_name
        elif serializer_name == "NestedSerializer" and isinstance(
            serializer, serializers.ModelSerializer
        ):
            ref_name = None
        else:
            ref_name = serializer_name
            if ref_name.endswith("Serializer"):
                ref_name = ref_name[: -len("Serializer")]
        return ref_name

    def get_writable_class(self, serializer):
        properties = {}
        fields = {} if hasattr(serializer, "child") else serializer.fields
        remove_fields = []

        for child_name, child in fields.items():
            # read_only fields don't need to be in writable (write only) serializers
            if "read_only" in dir(child) and child.read_only:
                remove_fields.append(child_name)
            if (
                isinstance(child, ChoiceField | WritableNestedSerializer)
                or isinstance(child, ManyRelatedField)
                and isinstance(child.child_relation, SerializedPKRelatedField)
            ):
                properties[child_name] = None

        if not properties:
            return None

        if type(serializer) not in self.writable_serializers:
            writable_name = "Writable" + type(serializer).__name__
            meta_class = getattr(type(serializer), "Meta", None)
            if meta_class:
                ref_name = "Writable" + self.get_serializer_ref_name(serializer)
                # remove read_only fields from write-only serializers
                fields = list(meta_class.fields)
                for field in remove_fields:
                    fields.remove(field)
                writable_meta = type(
                    "Meta", (meta_class,), {"ref_name": ref_name, "fields": fields}
                )

                properties["Meta"] = writable_meta

            self.writable_serializers[type(serializer)] = type(
                writable_name, (type(serializer),), properties
            )

        return self.writable_serializers[type(serializer)]

    def get_filter_backends(self):
        # bulk operations don't have filter params
        if self.is_bulk_action:
            return []
        return super().get_filter_backends()

    def _get_paginator(self):
        # bulk operations don't have pagination
        if self.is_bulk_action:
            return None
        return super()._get_paginator()

    def _get_request_body(self, direction="request"):
        # bulk delete should specify input
        if (not self.is_bulk_action) or (self.method != "DELETE"):
            return super()._get_request_body(direction)

        # rest from drf_spectacular.openapi.AutoSchema._get_request_body
        # but remove the unsafe method check

        request_serializer = self.get_request_serializer()

        if isinstance(request_serializer, dict):
            content = []
            request_body_required = True
            for media_type, serializer in request_serializer.items():
                (
                    schema,
                    partial_request_body_required,
                ) = self._get_request_for_media_type(serializer, direction)
                examples = self._get_examples(serializer, direction, media_type)
                if schema is None:
                    continue
                content.append((media_type, schema, examples))
                request_body_required &= partial_request_body_required
        else:
            schema, request_body_required = self._get_request_for_media_type(
                request_serializer, direction
            )
            if schema is None:
                return None
            content = [
                (
                    media_type,
                    schema,
                    self._get_examples(request_serializer, direction, media_type),
                )
                for media_type in self.map_parsers()
            ]

        request_body = {
            "content": {
                media_type: build_media_type_object(schema, examples)
                for media_type, schema, examples in content
            }
        }
        if request_body_required:
            request_body["required"] = request_body_required
        return request_body

    def get_description(self):
        """
        Return a string description for the ViewSet.
        """

        # Use docstring if it exists
        if self.view.__doc__:
            return get_doc(self.view.__class__)

        # When the action method is decorated with @action, use the docstring of the
        # method
        action_or_method = getattr(
            self.view, getattr(self.view, "action", self.method.lower()), None
        )
        if action_or_method and action_or_method.__doc__:
            return get_doc(action_or_method)

        return self._generate_description()

    def _generate_description(self):
        """
        Generate a docstring for the method.

        It also takes into account whether the method is for list or detail.
        """
        if not hasattr(self.view, "queryset"):
            return ""

        model_name = self.view.queryset.model._meta.verbose_name

        if "{id}" in self.path:
            return f"{self.method.capitalize()} a {model_name} object."
        return f"{self.method.capitalize()} a list of {model_name} objects."
