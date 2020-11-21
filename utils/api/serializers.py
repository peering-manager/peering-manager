from rest_framework import serializers

from .nested_serializers import NestedTagSerializer
from utils.models import Tag


class TagSerializer(serializers.ModelSerializer):
    tagged_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color", "comments", "tagged_items"]


class TaggedObjectSerializer(serializers.Serializer):
    tags = NestedTagSerializer(many=True, required=False)

    def _save_tags(self, instance, tags):
        if tags:
            instance.tags.set(*[t.name for t in tags])

        return instance

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        instance = super().create(validated_data)

        return self._save_tags(instance, tags)

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", [])
        instance = super().update(instance, validated_data)

        return self._save_tags(instance, tags)
