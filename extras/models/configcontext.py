from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from peering_manager.models import ChangeLoggedModel

__all__ = ("ConfigContext", "ConfigContextAssignment")


class ConfigContext(ChangeLoggedModel):
    """
    This model represents a set of arbitrary data available to an object type. Data is
    stored in JSON format.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    data = models.JSONField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("extras:configcontext_view", kwargs={"pk": self.pk})

    def clean(self):
        super().clean()

        # Verify that JSON data is provided as an object
        if not isinstance(self.data, dict):
            raise ValidationError(
                {"data": 'JSON data must be in object form. Example: {"foo": 123}'}
            )


class ConfigContextAssignment(ChangeLoggedModel):
    content_type = models.ForeignKey(to=ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey(ct_field="content_type", fk_field="object_id")
    config_context = models.ForeignKey(
        to="extras.ConfigContext", on_delete=models.PROTECT, related_name="assignments"
    )
    weight = models.PositiveSmallIntegerField(default=1000)

    class Meta:
        ordering = ["weight", "config_context"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "config_context"],
                name="configcontext_per_object",
            )
        ]

    def __str__(self):
        return str(self.config_context)
