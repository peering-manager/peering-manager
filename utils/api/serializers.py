from rest_framework import serializers

from utils.models import Tag


class TagSerializer(serializers.ModelSerializer):
    tagged_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color", "comments", "tagged_items"]
