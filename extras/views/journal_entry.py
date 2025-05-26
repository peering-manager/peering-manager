from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import JournalEntryFilterSet
from ..forms import JournalEntryBulkEditForm, JournalEntryFilterForm, JournalEntryForm
from ..models import JournalEntry
from ..tables import JournalEntryTable

__all__ = (
    "JournalEntryBulkDeleteView",
    "JournalEntryBulkEditView",
    "JournalEntryDeleteView",
    "JournalEntryEditView",
    "JournalEntryListView",
    "JournalEntryView",
)


@register_model_view(model=JournalEntry, name="list", path="", detail=False)
class JournalEntryListView(ObjectListView):
    permission_required = "extras.view_journalentry"
    queryset = JournalEntry.objects.all()
    filterset = JournalEntryFilterSet
    filterset_form = JournalEntryFilterForm
    table = JournalEntryTable
    template_name = "extras/journalentry/list.html"


@register_model_view(JournalEntry)
class JournalEntryView(ObjectView):
    permission_required = "extras.view_journalentry"
    queryset = JournalEntry.objects.all()


@register_model_view(model=JournalEntry, name="add", detail=False)
@register_model_view(model=JournalEntry, name="edit")
class JournalEntryEditView(ObjectEditView):
    queryset = JournalEntry.objects.all()
    form = JournalEntryForm


@register_model_view(JournalEntry, name="delete")
class JournalEntryDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_journalentry"
    queryset = JournalEntry.objects.all()


@register_model_view(model=JournalEntry, name="delete")
class JournalEntryBulkEditView(BulkEditView):
    permission_required = "extras.change_journalentry"
    queryset = JournalEntry.objects.all()
    filterset = JournalEntryFilterSet
    table = JournalEntryTable
    form = JournalEntryBulkEditForm


@register_model_view(JournalEntry, name="bulk_delete", path="delete", detail=False)
class JournalEntryBulkDeleteView(BulkDeleteView):
    permission_required = "extras.delete_journalentry"
    queryset = JournalEntry.objects.all()
    filterset = JournalEntryFilterSet
    table = JournalEntryTable
