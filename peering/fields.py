from __future__ import unicode_literals

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ASNField(models.BigIntegerField):
    description = "32-bit ASN field"
    default_validators = [
        MinValueValidator(1),
        MaxValueValidator(4294967295),
    ]
