from django.db import models

from .functions import validate_bgp_community


class CommunityField(models.CharField):
    description = "Community, Extended Community, or Large Community field"
    default_validators = [validate_bgp_community]
