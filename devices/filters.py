import django_filters

from utils.filters import (
    BaseFilterSet,
    CreatedUpdatedFilterSet,
    NameSlugSearchFilterSet,
)

from .enums import PasswordAlgorithm
from .models import Platform


class PlatformFilterSet(
    BaseFilterSet, CreatedUpdatedFilterSet, NameSlugSearchFilterSet
):
    password_algorithm = django_filters.MultipleChoiceFilter(
        choices=PasswordAlgorithm.choices, null_value=None
    )

    class Meta:
        model = Platform
        fields = ["id", "name", "slug", "napalm_driver", "description"]
