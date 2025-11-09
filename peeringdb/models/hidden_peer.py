from django.db import models
from django.urls import reverse
from django.utils import timezone

from peering_manager.models import ChangeLoggedModel

__all__ = ("HiddenPeer",)


class HiddenPeer(ChangeLoggedModel):
    """
    A model representing a network (AS) that is hidden on a specific IX LAN until a
    certain date.

    We decide to use a `IXLan` here instead of an `NetworkIXLan` because we want to be
    able to hide a network connected multiple times to the same `IXLan`.
    """

    peeringdb_network = models.ForeignKey(
        "peeringdb.Network",
        on_delete=models.CASCADE,
        related_name="hidden_on",
        verbose_name="PeeringDB network",
    )
    peeringdb_ixlan = models.ForeignKey(
        "peeringdb.IXLan",
        on_delete=models.CASCADE,
        related_name="hidden_peers",
        verbose_name="PeeringDB IX LAN",
    )
    until = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ["until", "peeringdb_network", "peeringdb_ixlan"]
        constraints = [
            models.UniqueConstraint(
                fields=["peeringdb_network", "peeringdb_ixlan"],
                name="network_ixlan_unique_hiddenpeer",
            )
        ]

    @property
    def is_expired(self) -> bool:
        return bool(self.until and self.until < timezone.now())

    def __str__(self) -> str:
        return f"{self.peeringdb_network} hidden on {self.peeringdb_ixlan}"

    def get_absolute_url(self) -> str:
        return reverse("peeringdb:hiddenpeer", args=[self.pk])
