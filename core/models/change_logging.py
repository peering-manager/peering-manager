from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe

from ..enums import ObjectChangeAction

if TYPE_CHECKING:
    from django.utils.safestring import SafeText

__all__ = ("ObjectChange",)


class ObjectChange(models.Model):
    """
    Records a change done to an object and the user who did it.
    """

    time = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)
    user = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="changes",
        blank=True,
        null=True,
    )
    user_name = models.CharField(max_length=150, editable=False)
    request_id = models.UUIDField(editable=False)
    action = models.CharField(max_length=50, choices=ObjectChangeAction)
    changed_object_type = models.ForeignKey(
        to=ContentType, on_delete=models.PROTECT, related_name="+"
    )
    changed_object_id = models.PositiveIntegerField()
    changed_object = GenericForeignKey(
        ct_field="changed_object_type", fk_field="changed_object_id"
    )
    related_object_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.PROTECT,
        related_name="+",
        blank=True,
        null=True,
    )
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object = GenericForeignKey(
        ct_field="related_object_type", fk_field="related_object_id"
    )
    object_repr = models.CharField(max_length=200, editable=False)
    prechange_data = models.JSONField(editable=False, blank=True, null=True)
    postchange_data = models.JSONField(editable=False, blank=True, null=True)

    class Meta:
        ordering = ["-time"]

    def __str__(self) -> str:
        return f"{self.changed_object_type} {self.object_repr} {self.get_action_display().lower()} by {self.user_name}"

    def save(self, *args, **kwargs) -> None:
        if not self.user_name:
            self.user_name = self.user.username
        if not self.object_repr:
            self.object_repr = str(self.changed_object)

        return super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("core:objectchange", args=[self.pk])

    def get_action_html(self) -> SafeText:
        """
        Return an HTML element based on the action.
        """
        match self.action:
            case ObjectChangeAction.CREATE:
                badge = "success"
            case ObjectChangeAction.UPDATE:
                badge = "primary"
            case ObjectChangeAction.DELETE:
                badge = "danger"
            case _:
                badge = "secondary"

        return mark_safe(
            f'<span class="badge text-bg-{badge}">{self.get_action_display() or "Unknown"}</span>'
        )

    @property
    def has_changes(self) -> bool:
        return self.prechange_data != self.postchange_data
