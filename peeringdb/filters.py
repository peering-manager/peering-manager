import django_filters

from .models import Synchronization


class SynchronizationFilter(django_filters.FilterSet):
    class Meta:
        model = Synchronization
        fields = ["time", "added", "updated", "deleted"]
