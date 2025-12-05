import django_filters
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .models import Token, TokenObjectPermission

__all__ = ("GroupFilterSet", "TokenObjectPermissionFilterSet", "UserFilterSet")


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
    group_id = django_filters.ModelMultipleChoiceFilter(
        field_name="groups",
        queryset=Group.objects.all(),
        label="Group",
    )
    group = django_filters.ModelMultipleChoiceFilter(
        field_name="groups__name",
        queryset=Group.objects.all(),
        to_field_name="name",
        label="Group (name)",
    )

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


class TokenObjectPermissionFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    token_id = django_filters.ModelMultipleChoiceFilter(
        field_name="token",
        queryset=Token.objects.all(),
        label="Token (ID)",
    )
    content_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name="content_type",
        queryset=ContentType.objects.all(),
        label="Content Type (ID)",
    )

    class Meta:
        model = TokenObjectPermission
        fields = [
            "id",
            "token",
            "content_type",
            "object_id",
            "can_view",
            "can_edit",
            "can_delete",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(token__key__icontains=value) | Q(object_id__icontains=value)
        )
