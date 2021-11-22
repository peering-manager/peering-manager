from rest_framework import serializers

from users.api.nested_serializers import UserNestedSerializer
from utils.enums import ObjectChangeAction
from utils.functions import get_serializer_for_model
from utils.models import ObjectChange, Tag

from .fields import ChoiceField, ContentTypeField
from .nested_serializers import NestedTagSerializer


class ObjectChangeSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="utils-api:objectchange-detail"
    )
    user = UserNestedSerializer(read_only=True)
    action = ChoiceField(choices=ObjectChangeAction.choices, read_only=True)
    changed_object_type = ContentTypeField(read_only=True)
    changed_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ObjectChange
        fields = [
            "id",
            "url",
            "time",
            "user",
            "user_name",
            "request_id",
            "action",
            "changed_object_type",
            "changed_object_id",
            "changed_object",
            "object_data",
        ]

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
        data = serializer(o.changed_object, context=context).data

        return data


class TagSerializer(serializers.ModelSerializer):
    tagged_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color", "comments", "tagged_items"]


class TaggedObjectSerializer(serializers.Serializer):
    tags = NestedTagSerializer(many=True, required=False)

    def _save_tags(self, instance, tags):
        if tags:
            instance.tags.set([t.name for t in tags])

        return instance

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        instance = super().create(validated_data)

        return self._save_tags(instance, tags)

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", [])
        instance = super().update(instance, validated_data)

        return self._save_tags(instance, tags)
