from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import ASN_MAX, ASN_MIN, TTL_MAX, TTL_MIN


class ASNField(models.BigIntegerField):
    description = "32-bit ASN field"

    def __init__(self, *args, **kwargs):
        allow_zero = kwargs.pop("allow_zero", False)
        self.default_validators = [
            MinValueValidator(ASN_MIN if not allow_zero else 0),
            MaxValueValidator(ASN_MAX),
        ]
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {"min_value": ASN_MIN, "max_value": ASN_MAX}
        defaults.update(**kwargs)
        return super().formfield(**defaults)


class TTLField(models.PositiveSmallIntegerField):
    description = "TTL field allowing value from 1 to 255"
    default_validators = [MinValueValidator(TTL_MIN), MaxValueValidator(TTL_MAX)]

    def formfield(self, **kwargs):
        defaults = {"min_value": TTL_MIN, "max_value": TTL_MAX}
        defaults.update(**kwargs)
        return super().formfield(**defaults)
