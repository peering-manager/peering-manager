from __future__ import annotations

from django.db import models
from django.utils.safestring import mark_safe

from peering_manager.enums import IPFamily
from peering_manager.models import OrganisationalModel

from ..enums import RoutingPolicyType

__all__ = ("RoutingPolicy",)


class RoutingPolicy(OrganisationalModel):
    type = models.CharField(
        max_length=50,
        choices=RoutingPolicyType,
        default=RoutingPolicyType.IMPORT,
    )
    weight = models.PositiveSmallIntegerField(default=0, help_text="The higher the number, the higher the priority")
    address_family = models.PositiveSmallIntegerField(default=IPFamily.ALL, choices=IPFamily)
    communities = models.ManyToManyField("Community", blank=True)

    class Meta:
        verbose_name_plural = "routing policies"
        ordering = ["-weight", "name"]

    def __str__(self) -> str:
        return self.name

    def get_type_html(self, display_name=False):
        if self.type == RoutingPolicyType.EXPORT:
            badge_type = "text-bg-primary"
            text = self.get_type_display()
        elif self.type == RoutingPolicyType.IMPORT:
            badge_type = "text-bg-info"
            text = self.get_type_display()
        elif self.type == RoutingPolicyType.IMPORT_EXPORT:
            badge_type = "text-bg-dark"
            text = self.get_type_display()
        else:
            badge_type = "text-bg-secondary"
            text = "Unknown"

        if display_name:
            text = self.name

        return mark_safe(f'<span class="badge {badge_type}">{text}</span>')
