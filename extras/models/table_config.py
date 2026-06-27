from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse

from peering_manager.models import ChangeLoggedModel

__all__ = ("TableConfig",)


class TableConfig(ChangeLoggedModel):
    """
    A default set of columns applied to a table for every user who has not
    customised it.
    """

    table = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the table class this configuration applies to",
    )
    object_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        related_name="table_configs",
        blank=True,
        null=True,
    )
    columns = ArrayField(
        base_field=models.CharField(max_length=100),
        help_text="Ordered list of column names to display by default",
    )

    class Meta:
        ordering = ["table"]

    def __str__(self) -> str:
        return self.table

    def get_absolute_url(self) -> str:
        return reverse("extras:tableconfig", args=[self.pk])
