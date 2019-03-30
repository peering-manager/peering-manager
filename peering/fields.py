from ipaddress import ip_network

from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models


class ASNField(models.BigIntegerField):
    description = "32-bit ASN field"
    default_validators = [MinValueValidator(1), MaxValueValidator(4294967295)]


class CommunityField(models.CharField):
    description = "BGP community or large community field"
    default_validators = [
        # BGP community and BGP large community
        RegexValidator(r"^(\d{1,5}:\d{1,5})|(\d{1,10}:\d{1,10}:\d{1,10}:\d{1,10})$")
    ]


class TTLField(models.PositiveSmallIntegerField):
    description = "TTL field allowing value from 0 to 255"
    default_validators = [MinValueValidator(1), MaxValueValidator(255)]
