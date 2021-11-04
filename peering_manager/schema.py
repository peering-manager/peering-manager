from drf_spectacular.extensions import (
    OpenApiSerializerFieldExtension,
    OpenApiViewExtension,
)
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema


class FixAPIRoot(OpenApiViewExtension):
    target_class = "peering_manager.api.views.APIRootView"

    def view_replacement(self):
        return extend_schema(responses=OpenApiTypes.OBJECT)(self.target_class)


class FixChoiceField(OpenApiSerializerFieldExtension):
    target_class = "peering_manager.api.fields.ChoiceField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)


class FixContentTypeField(OpenApiSerializerFieldExtension):
    target_class = "peering_manager.api.fields.ContentTypeField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)


class FixInetAddressField(OpenApiSerializerFieldExtension):
    target_class = "netfields.rest_framework.InetAddressField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)


class FixCidrAddressField(OpenApiSerializerFieldExtension):
    target_class = "netfields.rest_framework.CidrAddressField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)


class FixMACAddressField(OpenApiSerializerFieldExtension):
    target_class = "netfields.rest_framework.MACAddressField"

    def map_serializer_field(self, auto_schema, direction):
        return build_basic_type(OpenApiTypes.STR)
