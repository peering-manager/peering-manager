from django.db import models
from django.urls import reverse
from taggit.models import GenericTaggedItemBase, TagBase

from utils.enums import Colour
from utils.forms.fields import ColorField
from utils.models import ChangeLoggedMixin

__all__ = ("Tag", "TaggedItem")


class Tag(TagBase, ChangeLoggedMixin):
    color = ColorField(default=Colour.GREY)
    comments = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def get_absolute_url(self):
        return reverse("extras:tag_view", args=[self.pk])


class TaggedItem(GenericTaggedItemBase):
    tag = models.ForeignKey(
        to=Tag, related_name="%(app_label)s_%(class)s_items", on_delete=models.CASCADE
    )

    class Meta:
        index_together = ("content_type", "object_id")
