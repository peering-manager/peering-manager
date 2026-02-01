import contextlib

from django.db import models
from django.urls import reverse
from django.utils import timezone

from peering_manager.models import ChangeLoggedModel

from .peeringdb import IXLan, Network

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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hidden_on",
        verbose_name="PeeringDB network",
    )
    peeringdb_network_id_copy = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name="PeeringDB Network ID"
    )
    peeringdb_ixlan = models.ForeignKey(
        "peeringdb.IXLan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hidden_peers",
        verbose_name="PeeringDB IX LAN",
    )
    peeringdb_ixlan_id_copy = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name="PeeringDB IX LAN ID"
    )
    until = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ["until", "peeringdb_network", "peeringdb_ixlan"]
        constraints = [
            models.UniqueConstraint(
                fields=["peeringdb_network_id_copy", "peeringdb_ixlan_id_copy"],
                name="network_ixlan_unique_hiddenpeer",
            )
        ]

    @property
    def is_expired(self) -> bool:
        return bool(self.until and self.until < timezone.now())

    def __str__(self) -> str:
        network_str = (
            str(self.peeringdb_network)
            if self.peeringdb_network
            else f"Network ID {self.peeringdb_network_id_copy}"
        )
        ixlan_str = (
            str(self.peeringdb_ixlan)
            if self.peeringdb_ixlan
            else f"IX LAN ID {self.peeringdb_ixlan_id_copy}"
        )
        return f"{network_str} hidden on {ixlan_str}"

    def get_absolute_url(self) -> str:
        return reverse("peeringdb:hiddenpeer", args=[self.pk])

    def save(self, *args, **kwargs):
        if self.peeringdb_network:
            self.peeringdb_network_id_copy = self.peeringdb_network.pk
        if self.peeringdb_ixlan:
            self.peeringdb_ixlan_id_copy = self.peeringdb_ixlan.pk

        super().save(*args, **kwargs)

    def link_to_peeringdb(self) -> bool:
        changed_fields: list[str] = []

        if not self.peeringdb_network:
            with contextlib.suppress(Network.DoesNotExist):
                self.peeringdb_network = Network.objects.get(
                    pk=self.peeringdb_network_id_copy
                )
                changed_fields.append("peeringdb_network")
        if not self.peeringdb_ixlan:
            with contextlib.suppress(IXLan.DoesNotExist):
                self.peeringdb_ixlan = IXLan.objects.get(
                    pk=self.peeringdb_ixlan_id_copy
                )
                changed_fields.append("peeringdb_ixlan")

        if changed_fields:
            self.save(update_fields=changed_fields)

        return self.peeringdb_network and self.peeringdb_ixlan
