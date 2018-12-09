import json

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.core.serializers import serialize
from django.urls import reverse
from django.utils.safestring import mark_safe

from .constants import *
from .templatetags.helpers import title_with_uppers


class ChangeLoggedModel(models.Model):
    """
    Abstract class providing fields and functions to log changes made to a model.
    """

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True

    def serialize(self):
        """
        Return a JSON representation of an object using Django's built-in serializer.
        """
        return json.loads(serialize("json", [self]))[0]["fields"]

    def log_change(self, user, request_id, action):
        """
        Create a new ObjectChange representing a change made to this object.
        """
        ObjectChange(
            user=user,
            request_id=request_id,
            changed_object=self,
            action=action,
            object_data=self.serialize(),
        ).save()


class ObjectChange(models.Model):
    """
    Record a change done to an object and the user who did it.
    """

    time = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="changes",
        blank=True,
        null=True,
    )
    user_name = models.CharField(max_length=150, editable=False)
    request_id = models.UUIDField(editable=False)
    action = models.PositiveSmallIntegerField(choices=OBJECT_CHANGE_ACTION_CHOICES)
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
    object_repr = models.CharField(max_length=256, editable=False)
    object_data = JSONField(editable=False)

    class Meta:
        ordering = ["-time"]

    def save(self, *args, **kwargs):
        self.user_name = self.user.username
        self.object_repr = str(self.changed_object)

        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("utils:object_change_details", kwargs={"pk": self.pk})

    def get_html_icon(self):
        if self.action == OBJECT_CHANGE_ACTION_CREATE:
            return mark_safe('<i class="fas fa-plus-square text-success"></i>')
        if self.action == OBJECT_CHANGE_ACTION_UPDATE:
            return mark_safe('<i class="fas fa-pen-square text-warning"></i>')
        if self.action == OBJECT_CHANGE_ACTION_DELETE:
            return mark_safe('<i class="fas fa-minus-square text-danger"></i>')
        return mark_safe('<i class="fas fa-question-circle text-secondary"></i>')

    def __str__(self):
        return "{} {} {} by {}".format(
            title_with_uppers(self.changed_object_type),
            self.object_repr,
            self.get_action_display().lower(),
            self.user_name,
        )
