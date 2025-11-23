from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe

from peering_manager.models import OrganisationalModel

from ..enums import CommunityType
from ..fields import CommunityField
from ..functions import get_community_kind

__all__ = ("Community",)


class Community(OrganisationalModel):
    value = CommunityField(max_length=50)
    type = models.CharField(max_length=50, choices=CommunityType, blank=True, null=True)

    class Meta:
        verbose_name_plural = "communities"
        ordering = ["value", "name"]

    @property
    def kind(self) -> str | None:
        if not settings.VALIDATE_BGP_COMMUNITY_VALUE:
            return None
        try:
            return get_community_kind(self.value)
        except ValueError:
            return None

    def __str__(self) -> str:
        return self.name

    def get_type_html(self, display_name=False):
        if self.type == CommunityType.EGRESS:
            badge_type = "text-bg-primary"
            text = self.get_type_display()
        elif self.type == CommunityType.INGRESS:
            badge_type = "text-bg-info"
            text = self.get_type_display()
        else:
            badge_type = "text-bg-secondary"
            text = "Not set"

        if display_name:
            text = self.name

        return mark_safe(f'<span class="badge {badge_type}">{text}</span>')
