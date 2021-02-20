import django_filters

from utils.filters import (
    BaseFilterSet,
    CreatedUpdatedFilterSet,
    NameSlugSearchFilterSet,
)

from .models import Platform


class PlatformFilterSet(
    BaseFilterSet, CreatedUpdatedFilterSet, NameSlugSearchFilterSet
):
    class Meta:
        model = Platform
        fields = ["id", "name", "slug", "napalm_driver", "description"]
