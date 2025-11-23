from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.html import escape
from django.utils.safestring import mark_safe

from peering_manager.models import OrganisationalModel
from utils.enums import Colour
from utils.forms.fields import ColourField
from utils.templatetags.helpers import foreground_colour

if TYPE_CHECKING:
    from django.utils.safestring import SafeText


__all__ = ("Relationship",)


class Relationship(OrganisationalModel):
    color = ColourField(default=Colour.GREY)

    def get_html(self) -> SafeText:
        return mark_safe(
            f'<span class="badge" style="color: {foreground_colour(self.color)}; background-color: #{self.color}">{escape(self.name)}</span>'
        )
