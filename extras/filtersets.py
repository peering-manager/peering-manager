import django_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from peering_manager.filtersets import BaseFilterSet, ChangeLoggedModelFilterSet
from utils.filters import (
    ContentTypeFilter,
    MultiValueCharFilter,
    MultiValueNumberFilter,
)

from .enums import HttpMethod
from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    Tag,
    Webhook,
)

__all__ = (
    "ConfigContextFilterSet",
    "ConfigContextAssignmentFilterSet",
    "ExportTemplateFilterSet",
    "IXAPIFilterSet",
    "TagFilterSet",
    "WebhookFilterSet",
)


class ConfigContextFilterSet(ChangeLoggedModelFilterSet):
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


class ConfigContextAssignmentFilterSet(ChangeLoggedModelFilterSet):
    content_type = ContentTypeFilter()
    config_context_id = django_filters.ModelMultipleChoiceFilter(
        queryset=ConfigContext.objects.all(), label="Config Context (ID)"
    )

    class Meta:
        model = ConfigContextAssignment
        fields = ["id", "content_type_id", "object_id", "weight"]


class ExportTemplateFilterSet(ChangeLoggedModelFilterSet):
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


class IXAPIFilterSet(ChangeLoggedModelFilterSet):
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


class TagFilterSet(ChangeLoggedModelFilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    content_type = MultiValueCharFilter(method="_content_type")
    content_type_id = MultiValueNumberFilter(method="_content_type_id")

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color", "description"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(slug__icontains=value)
            | Q(description__icontains=value)
        )

    def _content_type(self, queryset, name, values):
        ct_filter = Q()

        # Compile list of app_label & model pairings
        for value in values:
            try:
                app_label, model = value.lower().split(".")
                ct_filter |= Q(app_label=app_label, model=model)
            except ValueError:
                pass

        content_types = ContentType.objects.filter(ct_filter)
        return queryset.filter(
            extras_taggeditem_items__content_type__in=content_types
        ).distinct()

    def _content_type_id(self, queryset, name, values):
        content_types = ContentType.objects.filter(pk__in=values)
        return queryset.filter(
            extras_taggeditem_items__content_type__in=content_types
        ).distinct()


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
