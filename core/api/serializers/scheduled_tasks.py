from peering_manager.api.serializers import (
    ValidatedModelSerializer,
    WritableNestedSerializer,
)

from ...models import ScheduledTask

__all__ = ("NestedScheduledTaskSerializer", "ScheduledTaskSerializer")


class ScheduledTaskSerializer(ValidatedModelSerializer):
    class Meta:
        model = ScheduledTask
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "task",
            "enabled",
            "interval",
            "created",
            "updated",
        ]


class NestedScheduledTaskSerializer(WritableNestedSerializer):
    class Meta:
        model = ScheduledTask
        fields = ["id", "url", "display_url", "display", "task"]
