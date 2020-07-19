from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models

from .constants import ASN_MIN, ASN_MAX


class ASNField(models.BigIntegerField):
    description = "32-bit ASN field"
    default_validators = [MinValueValidator(ASN_MIN), MaxValueValidator(ASN_MAX)]

    def formfield(self, **kwargs):
        defaults = {"min_value": ASN_MIN, "max_value": ASN_MAX}
        defaults.update(**kwargs)
        return super().formfield(**defaults)


class CommunityField(models.CharField):
    description = "Community, Extended Community, or BGP Large Community field"
    # TODO: make validators that actually match real community values
    # default_validators = [
    #     RegexValidator(r"^(\d{1,5}:\d{1,5})|(\d{1,10}:\d{1,10}:\d{1,10}:\d{1,10})$")
    # ]


class TTLField(models.PositiveSmallIntegerField):
    description = "TTL field allowing value from 1 to 255"
    default_validators = [MinValueValidator(1), MaxValueValidator(255)]
