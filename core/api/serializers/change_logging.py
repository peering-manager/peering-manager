from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from peering_manager.api.fields import ChoiceField, ContentTypeField
from peering_manager.api.serializers import BaseModelSerializer
from users.api.nested_serializers import NestedUserSerializer
from utils.api import get_serializer_for_model

from ...enums import *
from ...models import *

__all__ = ("ObjectChangeSerializer",)


class ObjectChangeSerializer(BaseModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="extras-api:objectchange-detail"
    )
    user = NestedUserSerializer(read_only=True)
    action = ChoiceField(choices=ObjectChangeAction, read_only=True)
    changed_object_type = ContentTypeField(read_only=True)
    changed_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ObjectChange
        fields = [
            "id",
            "url",
            "display",
            "time",
            "user",
            "user_name",
            "request_id",
            "action",
            "changed_object_type",
            "changed_object_id",
            "changed_object",
            "prechange_data",
            "postchange_data",
        ]

    @extend_schema_field(serializers.DictField)
    def get_changed_object(self, o):
        """
        Serialize a nested representation of the changed object.
        """
        if o.changed_object is None:
            return None

        try:
            serializer = get_serializer_for_model(o.changed_object, prefix="Nested")
        except Exception:
            return o.object_repr

        context = {"request": self.context["request"]}
        return serializer(o.changed_object, context=context).data
