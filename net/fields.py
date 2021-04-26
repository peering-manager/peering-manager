from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import VLAN_MAX, VLAN_MIN


class VLANField(models.PositiveSmallIntegerField):
    description = "Ethernet VLAN field"

    def __init__(self, *args, **kwargs):
        self.default_validators = [
            MinValueValidator(VLAN_MIN),
            MaxValueValidator(VLAN_MAX),
        ]
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {"min_value": VLAN_MIN, "max_value": VLAN_MAX}
        defaults.update(**kwargs)
        return super().formfield(**defaults)
