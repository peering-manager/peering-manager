from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.shortcuts import get_object_or_404

from peering.models import InternetExchange
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)

from .filtersets import (
    ConfigContextFilterSet,
    ExportTemplateFilterSet,
    IXAPIFilterSet,
    JournalEntryFilterSet,
    TagFilterSet,
    WebhookFilterSet,
)
from .forms import (
    ConfigContextAssignmentForm,
    ConfigContextFilterForm,
    ConfigContextForm,
    ExportTemplateFilterForm,
    ExportTemplateForm,
    IXAPIFilterForm,
    IXAPIForm,
    JournalEntryBulkEditForm,
    JournalEntryFilterForm,
    JournalEntryForm,
    TagBulkEditForm,
    TagFilterForm,
    TagForm,
    WebhookFilterForm,
    WebhookForm,
)
from .models import (
    IXAPI,
    ConfigContext,
    ConfigContextAssignment,
    ExportTemplate,
    JournalEntry,
    Tag,
    TaggedItem,
    Webhook,
)
from .tables import (
    ConfigContextAssignmentTable,
    ConfigContextTable,
    ExportTemplateTable,
    IXAPITable,
    JournalEntryTable,
    TaggedItemTable,
    TagTable,
    WebhookTable,
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
    tab = "main"

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
        assignments_table.configure(request)

        return {
            "assignments_table": assignments_table,
            "assignment_count": ConfigContextAssignment.objects.filter(
                config_context=instance
            ).count(),
            "configcontext_format": format,
        }


class ConfigContextEditView(ObjectEditView):
    queryset = ConfigContext.objects.all()
    form = ConfigContextForm


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
    form = ConfigContextAssignmentForm
    template_name = "extras/configcontextassignment/edit.html"

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
    tab = "config-context"

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
    tab = "main"


class ExportTemplateEditView(ObjectEditView):
    queryset = ExportTemplate.objects.all()
    form = ExportTemplateForm


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
    tab = "main"

    def get_extra_context(self, request, instance):
        return {
            "internet_exchange_points": InternetExchange.objects.filter(
                ixapi_endpoint=instance
            )
        }


class IXAPIEditView(ObjectEditView):
    queryset = IXAPI.objects.all()
    form = IXAPIForm
    template_name = "extras/ixapi/edit.html"


class IXAPIDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_ixapi"
    queryset = IXAPI.objects.all()


class JournalEntryListView(ObjectListView):
    permission_required = "extras.view_journalentry"
    queryset = JournalEntry.objects.all()
    filterset = JournalEntryFilterSet
    filterset_form = JournalEntryFilterForm
    table = JournalEntryTable
    template_name = "extras/journalentry/list.html"


class JournalEntryView(ObjectView):
    permission_required = "extras.view_journalentry"
    queryset = JournalEntry.objects.all()
    tab = "main"


class JournalEntryEditView(ObjectEditView):
    queryset = JournalEntry.objects.all()
    form = JournalEntryForm


class JournalEntryBulkEditView(BulkEditView):
    permission_required = "extras.change_journalentry"
    queryset = JournalEntry.objects.all()
    filterset = JournalEntryFilterSet
    table = JournalEntryTable
    form = JournalEntryBulkEditForm


class JournalEntryDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_journalentry"
    queryset = JournalEntry.objects.all()


class JournalEntryBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_journalentry"
    queryset = JournalEntry.objects.all()
    filterset = JournalEntryFilterSet
    table = JournalEntryTable


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
    tab = "main"

    def get_extra_context(self, request, instance):
        tagged_items = TaggedItem.objects.filter(tag=instance)
        taggeditem_table = TaggedItemTable(data=tagged_items, orderable=False)
        taggeditem_table.configure(request)

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
    queryset = Tag.objects.all()
    form = TagForm


class TagEdit(ObjectEditView):
    queryset = Tag.objects.all()
    form = TagForm


class TagBulkEdit(BulkEditView):
    permission_required = "extras.change_tag"
    queryset = Tag.objects.annotate(
        items=Count("extras_taggeditem_items", distinct=True)
    ).order_by("name")
    filterset = TagFilterSet
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


class WebhookList(ObjectListView):
    permission_required = "extras.view_webhook"
    queryset = Webhook.objects.all()
    filterset = WebhookFilterSet
    filterset_form = WebhookFilterForm
    table = WebhookTable
    template_name = "extras/webhook/list.html"


class WebhookView(ObjectView):
    permission_required = "extras.view_webhook"
    queryset = Webhook.objects.all()
    tab = "main"


class WebhookAdd(ObjectEditView):
    queryset = Webhook.objects.all()
    form = WebhookForm


class WebhookEdit(ObjectEditView):
    queryset = Webhook.objects.all()
    form = WebhookForm


class WebhookDelete(ObjectDeleteView):
    permission_required = "extras.delete_webhook"
    queryset = Webhook.objects.all()
