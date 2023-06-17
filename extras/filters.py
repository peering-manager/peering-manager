import django_filters
from django.contrib.auth.models import User
from django.db.models import Q

from utils.filters import (
    BaseFilterSet,
    ContentTypeFilter,
    CreatedUpdatedFilterSet,
    NameSlugSearchFilterSet,
)

from .enums import HttpMethod, ObjectChangeAction
from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    ObjectChange,
    Tag,
    Webhook,
)


class ConfigContextFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ConfigContext
        fields = ["id", "name", "description", "is_active"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class ConfigContextAssignmentFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    content_type = ContentTypeFilter()
    config_context_id = django_filters.ModelMultipleChoiceFilter(
        queryset=ConfigContext.objects.all(), label="Config Context (ID)"
    )

    class Meta:
        model = ConfigContextAssignment
        fields = ["id", "content_type_id", "object_id", "weight"]


class ExportTemplateFilterSet(BaseFilterSet, CreatedUpdatedFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = ExportTemplate
        fields = ["id", "name", "description"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )


class IXAPIFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        model = IXAPI
        fields = ["id", "name", "url", "api_key"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(url__icontains=value)
            | Q(api_key__icontains=value)
        )


class ObjectChangeFilterSet(BaseFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    time = django_filters.DateTimeFromToRangeFilter()
    action = django_filters.MultipleChoiceFilter(
        choices=ObjectChangeAction, null_value=None
    )
    user_id = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(), label="User (ID)"
    )
    user = django_filters.ModelMultipleChoiceFilter(
        field_name="user__username",
        queryset=User.objects.all(),
        to_field_name="username",
        label="User name",
    )

    class Meta:
        model = ObjectChange
        fields = [
            "id",
            "user",
            "user_name",
            "request_id",
            "action",
            "changed_object_type_id",
            "changed_object_id",
            "object_repr",
        ]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(user_name__icontains=value) | Q(object_repr__icontains=value)
        )


class TagFilterSet(BaseFilterSet, NameSlugSearchFilterSet):
    class Meta:
        model = Tag
        fields = ["id", "color"]


class WebhookFilterSet(BaseFilterSet):
    http_method = django_filters.MultipleChoiceFilter(choices=HttpMethod)

    class Meta:
        model = Webhook
        fields = [
            "id",
            "name",
            "type_create",
            "type_update",
            "type_delete",
            "enabled",
            "http_method",
            "http_content_type",
            "secret",
            "ssl_verification",
            "ca_file_path",
        ]
