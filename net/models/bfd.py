from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from peering_manager.models import OrganisationalModel

__all__ = ("BFD",)


class BFD(OrganisationalModel):
    minimum_transmit_interval = models.PositiveIntegerField(
        help_text="Minimum transmit interval in milliseconds",
        default=300,
        validators=[MinValueValidator(1), MaxValueValidator(255000)],
    )
    minimum_receive_interval = models.PositiveIntegerField(
        help_text="Minimum receive interval in milliseconds",
        default=300,
        validators=[MinValueValidator(1), MaxValueValidator(255000)],
    )
    detection_multiplier = models.PositiveSmallIntegerField(
        help_text="Number of missed messages before declaring a session down",
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(255)],
    )
    hold_time = models.PositiveIntegerField(
        help_text="How long a session must remain up in milliseconds before state change",
        default=0,
        validators=[MaxValueValidator(255000)],
    )

    class Meta:
        verbose_name = "BFD configuration"
