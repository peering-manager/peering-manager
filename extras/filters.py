import django_filters
from django.db.models import Q

from utils.filters import BaseFilterSet, ContentTypeFilter, CreatedUpdatedFilterSet

from .enums import HttpMethod
from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
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
