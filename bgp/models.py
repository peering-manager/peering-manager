from django.urls import reverse
from django.utils.safestring import mark_safe

from peering_manager.models import OrganisationalModel
from utils.enums import Colour
from utils.forms.fields import ColourField
from utils.templatetags.helpers import foreground_color

__all__ = ("Relationship",)


class Relationship(OrganisationalModel):
    color = ColourField(default=Colour.GREY)

    def get_absolute_url(self):
        return reverse("bgp:relationship_view", args=[self.pk])

    def get_html(self):
        return mark_safe(
            f'<span class="badge" style="color: {foreground_color(self.color)}; background-color: #{self.color}">{self.name}</span>'
        )
