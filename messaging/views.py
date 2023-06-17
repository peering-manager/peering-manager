from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from messaging.filters import ContactFilterSet, ContactRoleFilterSet, EmailFilterSet
from messaging.forms import (
    ContactAssignmentForm,
    ContactBulkEditForm,
    ContactFilterForm,
    ContactForm,
    ContactRoleBulkEditForm,
    ContactRoleFilterForm,
    ContactRoleForm,
    EmailFilterForm,
    EmailForm,
)
from messaging.models import Contact, ContactAssignment, ContactRole, Email
from messaging.tables import (
    ContactAssignmentTable,
    ContactRoleTable,
    ContactTable,
    EmailTable,
)
from peering_manager.views.generics import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.functions import count_related
from utils.tables import paginate_table


class ContactRoleList(ObjectListView):
    permission_required = "messaging.view_contactrole"
    queryset = ContactRole.objects.all()
    filterset = ContactRoleFilterSet
    filterset_form = ContactRoleFilterForm
    table = ContactRoleTable
    template_name = "messaging/contactrole/list.html"


class ContactRoleView(ObjectView):
    permission_required = "messaging.view_contactrole"
    queryset = ContactRole.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class ContactRoleAdd(ObjectEditView):
    permission_required = "messaging.add_contactrole"
    queryset = ContactRole.objects.all()
    model_form = ContactRoleForm
    template_name = "messaging/contactrole/add_edit.html"


class ContactRoleBulkEdit(BulkEditView):
    permission_required = "messaging.change_contactrole"
    queryset = ContactRole.objects.all()
    filterset = ContactRoleFilterSet
    table = ContactRoleTable
    form = ContactRoleBulkEditForm


class ContactRoleEdit(ObjectEditView):
    permission_required = "messaging.change_contactrole"
    queryset = ContactRole.objects.all()
    model_form = ContactRoleForm
    template_name = "messaging/contactrole/add_edit.html"


class ContactRoleDelete(ObjectDeleteView):
    permission_required = "messaging.delete_contactrole"
    queryset = ContactRole.objects.all()


class ContactRoleBulkDelete(BulkDeleteView):
    permission_required = "messaging.delete_contactrole"
    queryset = ContactRole.objects.all()
    filterset = ContactRoleFilterSet
    table = ContactRoleTable


class ContactList(ObjectListView):
    permission_required = "messaging.view_contact"
    queryset = Contact.objects.annotate(
        assignment_count=count_related(ContactAssignment, "contact")
    )
    filterset = ContactFilterSet
    filterset_form = ContactFilterForm
    table = ContactTable
    template_name = "messaging/contact/list.html"


class ContactView(ObjectView):
    permission_required = "messaging.view_contact"
    queryset = Contact.objects.all()

    def get_extra_context(self, request, instance):
        contact_assignments = ContactAssignment.objects.filter(contact=instance)
        assignments_table = ContactAssignmentTable(contact_assignments)
        assignments_table.columns.hide("contact")
        paginate_table(assignments_table, request)

        return {
            "assignments_table": assignments_table,
            "assignment_count": ContactAssignment.objects.filter(
                contact=instance
            ).count(),
            "active_tab": "main",
        }


class ContactAdd(ObjectEditView):
    permission_required = "messaging.add_contact"
    queryset = Contact.objects.all()
    model_form = ContactForm
    template_name = "messaging/contact/add_edit.html"


class ContactEdit(ObjectEditView):
    permission_required = "messaging.change_contact"
    queryset = Contact.objects.all()
    model_form = ContactForm
    template_name = "messaging/contact/add_edit.html"


class ContactBulkEdit(BulkEditView):
    permission_required = "messaging.change_contact"
    queryset = Contact.objects.annotate(
        assignment_count=count_related(ContactAssignment, "contact")
    )
    filterset = ContactFilterSet
    table = ContactTable
    form = ContactBulkEditForm


class ContactDelete(ObjectDeleteView):
    permission_required = "messaging.delete_contact"
    queryset = Contact.objects.all()


class ContactBulkDelete(BulkDeleteView):
    permission_required = "messaging.delete_contact"
    queryset = Contact.objects.annotate(
        assignment_count=count_related(ContactAssignment, "contact")
    )
    filterset = ContactFilterSet
    table = ContactTable


class ContactAssignmentEditView(ObjectEditView):
    permission_required = "messaging.change_contactassignment"
    queryset = ContactAssignment.objects.all()
    model_form = ContactAssignmentForm
    template_name = "messaging/contactassignment/add_edit.html"

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            content_type = get_object_or_404(
                ContentType, pk=request.GET.get("content_type")
            )
            instance.object = get_object_or_404(
                content_type.model_class(), pk=request.GET.get("object_id")
            )
        return instance


class ContactAssignmentDeleteView(ObjectDeleteView):
    permission_required = "messaging.delete_contactassignment"
    queryset = ContactAssignment.objects.all()


class EmailList(ObjectListView):
    permission_required = "messaging.view_email"
    queryset = Email.objects.all()
    filterset = EmailFilterSet
    filterset_form = EmailFilterForm
    table = EmailTable
    template_name = "messaging/email/list.html"


class EmailView(ObjectView):
    permission_required = "messaging.view_email"
    queryset = Email.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class EmailAdd(ObjectEditView):
    permission_required = "messaging.add_email"
    queryset = Email.objects.all()
    model_form = EmailForm
    template_name = "messaging/email/add_edit.html"


class EmailEdit(ObjectEditView):
    permission_required = "messaging.change_email"
    queryset = Email.objects.all()
    model_form = EmailForm
    template_name = "messaging/email/add_edit.html"


class EmailDelete(ObjectDeleteView):
    permission_required = "messaging.delete_email"
    queryset = Email.objects.all()


class EmailBulkDelete(BulkDeleteView):
    permission_required = "messaging.delete_email"
    queryset = Email.objects.all()
    filterset = EmailFilterSet
    table = EmailTable
