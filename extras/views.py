from django import template
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import View
from django_tables2 import RequestConfig

from peering.models import InternetExchange
from peering_manager.views.generics import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
    PermissionRequiredMixin,
)
from utils.functions import shallow_compare_dict
from utils.paginators import EnhancedPaginator, get_paginate_count
from utils.tables import paginate_table

from .filters import (
    ConfigContextFilterSet,
    ExportTemplateFilterSet,
    IXAPIFilterSet,
    ObjectChangeFilterSet,
    TagFilterSet,
)
from .forms import (
    ConfigContextAssignmentForm,
    ConfigContextFilterForm,
    ConfigContextForm,
    ExportTemplateFilterForm,
    ExportTemplateForm,
    IXAPIFilterForm,
    IXAPIForm,
    ObjectChangeFilterForm,
    TagBulkEditForm,
    TagFilterForm,
    TagForm,
)
from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    ObjectChange,
    Tag,
    TaggedItem,
)
from .tables import (
    ConfigContextAssignmentTable,
    ConfigContextTable,
    ExportTemplateTable,
    IXAPITable,
    ObjectChangeTable,
    TaggedItemTable,
    TagTable,
)


class ConfigContextListView(ObjectListView):
    permission_required = "extras.view_configcontext"
    queryset = ConfigContext.objects.all()
    filterset = ConfigContextFilterSet
    filterset_form = ConfigContextFilterForm
    table = ConfigContextTable
    template_name = "extras/configcontext/list.html"


class ConfigContextView(ObjectView):
    permission_required = "extras.view_configcontext"
    queryset = ConfigContext.objects.all()

    def get_extra_context(self, request, instance):
        if request.GET.get("format") in ("json", "yaml"):
            format = request.GET.get("format")
            if request.user.is_authenticated:
                request.user.preferences.set(
                    "configcontext.format", format, commit=True
                )
        elif request.user.is_authenticated:
            format = request.user.preferences.get("configcontext.format", "json")
        else:
            format = "json"

        config_context_assignments = ConfigContextAssignment.objects.filter(
            config_context=instance
        )
        assignments_table = ConfigContextAssignmentTable(config_context_assignments)
        assignments_table.columns.hide("config_context")
        paginate_table(assignments_table, request)

        return {
            "assignments_table": assignments_table,
            "assignment_count": ConfigContextAssignment.objects.filter(
                config_context=instance
            ).count(),
            "configcontext_format": format,
            "active_tab": "main",
        }


class ConfigContextAddView(ObjectEditView):
    permission_required = "extras.add_configcontext"
    queryset = ConfigContext.objects.all()
    model_form = ConfigContextForm
    template_name = "extras/configcontext/add_edit.html"


class ConfigContextEditView(ObjectEditView):
    permission_required = "extras.change_configcontext"
    queryset = ConfigContext.objects.all()
    model_form = ConfigContextForm
    template_name = "extras/configcontext/add_edit.html"


class ConfigContextDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_configcontext"
    queryset = ConfigContext.objects.all()


class ConfigContextBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_configcontext"
    queryset = ConfigContext.objects.all()
    filterset = ConfigContextFilterSet
    table = ConfigContextTable


class ConfigContextAssignmentEditView(ObjectEditView):
    permission_required = "extras.edit_configcontextassignment"
    queryset = ConfigContextAssignment.objects.all()
    model_form = ConfigContextAssignmentForm
    template_name = "extras/configcontextassignment/add_edit.html"

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            content_type = get_object_or_404(
                ContentType, pk=request.GET.get("content_type")
            )
            instance.object = get_object_or_404(
                content_type.model_class(), pk=request.GET.get("object_id")
            )
        return instance


class ConfigContextAssignmentDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_configcontextassignment"
    queryset = ConfigContextAssignment.objects.all()


class ObjectConfigContextView(ObjectView):
    base_template = None
    template_name = "extras/object_configcontext.html"

    def get_extra_context(self, request, instance):
        if request.GET.get("format") in ("json", "yaml"):
            format = request.GET.get("format")
            if request.user.is_authenticated:
                request.user.preferences.set(
                    "configcontext.format", format, commit=True
                )
        elif request.user.is_authenticated:
            format = request.user.preferences.get("configcontext.format", "json")
        else:
            format = "json"

        return {
            "configcontext_format": format,
            "base_template": self.base_template,
            "active_tab": "config-context",
            "rendered_context": instance.get_config_context(),
        }


class ExportTemplateListView(ObjectListView):
    permission_required = "extras.view_exporttemplate"
    queryset = ExportTemplate.objects.all()
    filterset = ExportTemplateFilterSet
    filterset_form = ExportTemplateFilterForm
    table = ExportTemplateTable
    template_name = "extras/exporttemplate/list.html"


class ExportTemplateView(ObjectView):
    permission_required = "extras.view_exporttemplate"
    queryset = ExportTemplate.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class ExportTemplateAddView(ObjectEditView):
    permission_required = "extras.add_exporttemplate"
    queryset = ExportTemplate.objects.all()
    model_form = ExportTemplateForm
    template_name = "extras/exporttemplate/add_edit.html"


class ExportTemplateEditView(ObjectEditView):
    permission_required = "extras.change_exporttemplate"
    queryset = ExportTemplate.objects.all()
    model_form = ExportTemplateForm
    template_name = "extras/exporttemplate/add_edit.html"


class ExportTemplateDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_exporttemplate"
    queryset = ExportTemplate.objects.all()


class ExportTemplateBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_exporttemplate"
    queryset = ExportTemplate.objects.all()
    filterset = ExportTemplateFilterSet
    table = ExportTemplateTable


class IXAPIListView(ObjectListView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()
    filterset = IXAPIFilterSet
    filterset_form = IXAPIFilterForm
    table = IXAPITable
    template_name = "extras/ixapi/list.html"


class IXAPIView(ObjectView):
    permission_required = "extras.view_ixapi"
    queryset = IXAPI.objects.all()

    def get_extra_context(self, request, instance):
        return {
            "internet_exchange_points": InternetExchange.objects.filter(
                ixapi_endpoint=instance
            ),
            "active_tab": "main",
        }


class IXAPIAddView(ObjectEditView):
    permission_required = "extras.add_ixapi"
    queryset = IXAPI.objects.all()
    model_form = IXAPIForm
    template_name = "extras/ixapi/add_edit.html"


class IXAPIEditView(ObjectEditView):
    permission_required = "extras.change_ixapi"
    queryset = IXAPI.objects.all()
    model_form = IXAPIForm
    template_name = "extras/ixapi/add_edit.html"


class IXAPIDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_ixapi"
    queryset = IXAPI.objects.all()


class ObjectChangeList(ObjectListView):
    permission_required = "extras.view_objectchange"
    queryset = ObjectChange.objects.select_related("user").prefetch_related(
        "changed_object"
    )
    filterset = ObjectChangeFilterSet
    filterset_form = ObjectChangeFilterForm
    table = ObjectChangeTable
    template_name = "utils/object_change/list.html"


class ObjectChangeLog(View):
    def get(self, request, model, **kwargs):
        # Get object by model and kwargs (like asn=64500)
        obj = get_object_or_404(model, **kwargs)

        # Gather all changes for this object (and its related objects)
        content_type = ContentType.objects.get_for_model(model)
        objectchanges = ObjectChange.objects.select_related(
            "user", "changed_object_type"
        ).filter(
            Q(changed_object_type=content_type, changed_object_id=obj.pk)
            | Q(related_object_type=content_type, related_object_id=obj.pk)
        )
        objectchanges_table = ObjectChangeTable(data=objectchanges, orderable=False)

        # Apply the request context
        paginate = {
            "paginator_class": EnhancedPaginator,
            "per_page": get_paginate_count(request),
        }
        RequestConfig(request, paginate).configure(objectchanges_table)

        # Check whether a header template exists for this model
        base_template = f"{model._meta.app_label}/{model._meta.model_name}/_base.html"
        try:
            template.loader.get_template(base_template)
        except template.TemplateDoesNotExist:
            base_template = "_base.html"

        return render(
            request,
            "utils/object_change/log.html",
            {
                "instance": obj,
                "table": objectchanges_table,
                "base_template": base_template,
                "active_tab": "changelog",
            },
        )


class ObjectChangeView(PermissionRequiredMixin, View):
    permission_required = "extras.view_objectchange"

    def get(self, request, pk):
        instance = get_object_or_404(ObjectChange, pk=pk)

        related_changes = ObjectChange.objects.filter(
            request_id=instance.request_id
        ).exclude(pk=instance.pk)
        related_changes_table = ObjectChangeTable(
            data=related_changes[:50], orderable=False
        )

        object_changes = ObjectChange.objects.filter(
            changed_object_type=instance.changed_object_type,
            changed_object_id=instance.changed_object_id,
        )

        next_change = (
            object_changes.filter(time__gt=instance.time).order_by("time").first()
        )
        previous_change = (
            object_changes.filter(time__lt=instance.time).order_by("-time").first()
        )

        if (
            not instance.prechange_data
            and instance.action in ["update", "delete"]
            and previous_change
        ):
            non_atomic_change = True
            prechange_data = previous_change.postchange_data
        else:
            non_atomic_change = False
            prechange_data = instance.prechange_data

        if prechange_data and instance.postchange_data:
            diff_added = shallow_compare_dict(
                prechange_data or dict(),
                instance.postchange_data or dict(),
                exclude=["updated"],
            )
            diff_removed = (
                {x: prechange_data.get(x) for x in diff_added} if prechange_data else {}
            )
        else:
            diff_added = None
            diff_removed = None

        return render(
            request,
            "utils/object_change/details.html",
            {
                "instance": instance,
                "diff_added": diff_added,
                "diff_removed": diff_removed,
                "next_change": next_change,
                "previous_change": previous_change,
                "related_changes_table": related_changes_table,
                "related_changes_count": related_changes.count(),
                "non_atomic_change": non_atomic_change,
            },
        )


class TagList(ObjectListView):
    permission_required = "extras.view_tag"
    queryset = Tag.objects.annotate(
        items=Count("extras_taggeditem_items", distinct=True)
    ).order_by("name")
    filterset = TagFilterSet
    filterset_form = TagFilterForm
    table = TagTable
    template_name = "extras/tag/list.html"


class TagView(ObjectView):
    permission_required = "extras.view_tag"
    queryset = Tag.objects.all()

    def get_extra_context(self, request, instance):
        tagged_items = TaggedItem.objects.filter(tag=instance)
        taggeditem_table = TaggedItemTable(data=tagged_items, orderable=False)
        paginate_table(taggeditem_table, request)

        object_types = [
            {
                "content_type": ContentType.objects.get(pk=ti["content_type"]),
                "item_count": ti["item_count"],
            }
            for ti in tagged_items.values("content_type").annotate(
                item_count=Count("pk")
            )
        ]

        return {
            "taggeditem_table": taggeditem_table,
            "tagged_item_count": tagged_items.count(),
            "object_types": object_types,
        }


class TagAdd(ObjectEditView):
    permission_required = "extras.add_tag"
    queryset = Tag.objects.all()
    model_form = TagForm
    template_name = "extras/tag/add_edit.html"


class TagEdit(ObjectEditView):
    permission_required = "extras.change_tag"
    queryset = Tag.objects.all()
    model_form = TagForm
    template_name = "extras/tag/add_edit.html"


class TagBulkEdit(BulkEditView):
    permission_required = "extras.change_tag"
    queryset = Tag.objects.annotate(
        items=Count("extras_taggeditem_items", distinct=True)
    ).order_by("name")
    filter = TagFilterSet
    table = TagTable
    form = TagBulkEditForm


class TagDelete(ObjectDeleteView):
    permission_required = "extras.delete_tag"
    queryset = Tag.objects.all()


class TagBulkDelete(BulkDeleteView):
    permission_required = "extras.delete_tag"
    queryset = Tag.objects.annotate(
        items=Count("extras_taggeditem_items", distinct=True)
    ).order_by("name")
    filterset = TagFilterSet
    table = TagTable
