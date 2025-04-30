from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.functions import count_related
from utils.views import register_model_view

from ..filtersets import ContactFilterSet
from ..forms import ContactBulkEditForm, ContactFilterForm, ContactForm
from ..models import Contact, ContactAssignment
from ..tables import ContactAssignmentTable, ContactTable

__all__ = (
    "ContactBulkDelete",
    "ContactBulkEdit",
    "ContactDelete",
    "ContactEdit",
    "ContactList",
    "ContactView",
)


@register_model_view(model=Contact, name="list", path="", detail=False)
class ContactList(ObjectListView):
    permission_required = "messaging.view_contact"
    queryset = Contact.objects.annotate(
        assignment_count=count_related(ContactAssignment, "contact")
    )
    filterset = ContactFilterSet
    filterset_form = ContactFilterForm
    table = ContactTable
    template_name = "messaging/contact/list.html"


@register_model_view(model=Contact)
class ContactView(ObjectView):
    permission_required = "messaging.view_contact"
    queryset = Contact.objects.all()

    def get_extra_context(self, request, instance):
        contact_assignments = ContactAssignment.objects.filter(contact=instance)
        assignments_table = ContactAssignmentTable(contact_assignments)
        assignments_table.columns.hide("contact")
        assignments_table.configure(request)

        return {
            "assignments_table": assignments_table,
            "assignment_count": ContactAssignment.objects.filter(
                contact=instance
            ).count(),
        }


@register_model_view(model=Contact, name="add", detail=False)
@register_model_view(model=Contact, name="edit")
class ContactEdit(ObjectEditView):
    queryset = Contact.objects.all()
    form = ContactForm


@register_model_view(model=Contact, name="delete")
class ContactDelete(ObjectDeleteView):
    permission_required = "messaging.delete_contact"
    queryset = Contact.objects.all()


@register_model_view(model=Contact, name="bulk_edit", path="edit", detail=False)
class ContactBulkEdit(BulkEditView):
    permission_required = "messaging.change_contact"
    queryset = Contact.objects.annotate(
        assignment_count=count_related(ContactAssignment, "contact")
    )
    filterset = ContactFilterSet
    table = ContactTable
    form = ContactBulkEditForm


@register_model_view(model=Contact, name="bulk_delete", path="delete", detail=False)
class ContactBulkDelete(BulkDeleteView):
    queryset = Contact.objects.annotate(
        assignment_count=count_related(ContactAssignment, "contact")
    )
    filterset = ContactFilterSet
    table = ContactTable
