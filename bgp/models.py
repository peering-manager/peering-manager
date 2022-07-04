from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe

from utils.enums import Color
from utils.forms.fields import ColorField
from utils.models import ChangeLoggedMixin
from utils.templatetags.helpers import foreground_color

__all__ = ("Relationship",)


class Relationship(ChangeLoggedMixin):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)
    color = ColorField(default=Color.GREY)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("bgp:relationship_view", args=[self.pk])

    def get_html(self):
        return mark_safe(
            f'<span class="badge" style="color: {foreground_color(self.color)}; background-color: #{self.color}">{self.name}</span>'
        )
