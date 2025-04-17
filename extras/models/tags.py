from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from taggit.models import GenericTaggedItemBase, TagBase

from peering_manager.models import ChangeLoggedModel
from utils.enums import Colour
from utils.forms.fields import ColourField

__all__ = ("Tag", "TaggedItem")


class Tag(TagBase, ChangeLoggedModel):
    color = ColourField(default=Colour.GREY)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]

    def get_absolute_url(self) -> str:
        return reverse("extras:tag", args=[self.pk])

    def slugify(self, tag, i=None) -> str:
        # Allow Unicode in Tag slugs (avoids empty slugs for Tags with all-Unicode names)
        slug = slugify(tag, allow_unicode=True)
        if i is not None:
            slug += f"_{i:d}"
        return slug


class TaggedItem(GenericTaggedItemBase):
    tag = models.ForeignKey(
        to=Tag, related_name="%(app_label)s_%(class)s_items", on_delete=models.CASCADE
    )

    class Meta:
        indexes = [models.Index(fields=["content_type", "object_id"])]
