import django_filters
from django.contrib.auth.models import Group, User
from django.db.models import Q


class GroupFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = Group
        fields = ["id", "name"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(name__icontains=value)


class UserFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(username__icontains=value)
            | Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(email__icontains=value)
        )
