from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

from utils.enums import Color, ObjectChangeAction
from utils.forms.fields import ColorField
from utils.functions import serialize_object


class ChangeLoggedModel(models.Model):
    """
    Abstract class providing fields and functions to log changes made to a model.
    """

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True

    def snapshot(self):
        """
        Save a snapshot of the object's current state in preparation for modification.
        """
        self._prechange_snapshot = serialize_object(self)

    def to_objectchange(self, action, related_object=None):
        """
        Return a new `ObjectChange` representing a change made to this object.
        """
        object_change = ObjectChange(
            changed_object=self,
            related_object=related_object,
            object_repr=str(self),
            action=action,
        )

        if hasattr(self, "_prechange_snapshot"):
            object_change.prechange_data = self._prechange_snapshot
        if action in (ObjectChangeAction.CREATE, ObjectChangeAction.UPDATE):
            object_change.postchange_data = serialize_object(self)

        return object_change


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
    action = models.CharField(max_length=50, choices=ObjectChangeAction.choices)
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

    def __str__(self):
        return f"{self.changed_object_type} {self.object_repr} {self.get_action_display().lower()} by {self.user_name}"

    def save(self, *args, **kwargs):
        if not self.user_name:
            self.user_name = self.user.username
        if not self.object_repr:
            self.object_repr = str(self.changed_object)

        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("utils:objectchange_view", args=[self.pk])

    def get_html_icon(self):
        icon = '<i class="fas fa-question-circle text-secondary"></i>'
        if self.action == ObjectChangeAction.CREATE:
            icon = '<i class="fas fa-plus-square text-success"></i>'
        if self.action == ObjectChangeAction.UPDATE:
            icon = '<i class="fas fa-pen-square text-warning"></i>'
        if self.action == ObjectChangeAction.DELETE:
            icon = '<i class="fas fa-minus-square text-danger"></i>'
        return mark_safe(icon)


class Tag(TagBase, ChangeLoggedModel):
    color = ColorField(default=Color.GREY)
    comments = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def get_absolute_url(self):
        return reverse("utils:tag_view", args=[self.pk])


class TaggedItem(GenericTaggedItemBase):
    tag = models.ForeignKey(
        to=Tag, related_name="%(app_label)s_%(class)s_items", on_delete=models.CASCADE
    )

    class Meta:
        index_together = ("content_type", "object_id")


class TaggableModel(models.Model):
    """
    Abstract class that just provides tags to its subclasses.
    """

    tags = TaggableManager(through=TaggedItem)

    class Meta:
        abstract = True
