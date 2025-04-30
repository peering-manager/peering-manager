from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import ContactRoleFilterSet
from ..forms import ContactRoleBulkEditForm, ContactRoleFilterForm, ContactRoleForm
from ..models import ContactRole
from ..tables import ContactRoleTable

__all__ = (
    "ContactRoleBulkDelete",
    "ContactRoleBulkEdit",
    "ContactRoleDelete",
    "ContactRoleEdit",
    "ContactRoleList",
    "ContactRoleView",
)


@register_model_view(model=ContactRole, name="list", path="", detail=False)
class ContactRoleList(ObjectListView):
    permission_required = "messaging.view_contactrole"
    queryset = ContactRole.objects.all()
    filterset = ContactRoleFilterSet
    filterset_form = ContactRoleFilterForm
    table = ContactRoleTable
    template_name = "messaging/contactrole/list.html"


@register_model_view(model=ContactRole)
class ContactRoleView(ObjectView):
    permission_required = "messaging.view_contactrole"
    queryset = ContactRole.objects.all()


@register_model_view(model=ContactRole, name="add", detail=False)
@register_model_view(model=ContactRole, name="edit")
class ContactRoleEdit(ObjectEditView):
    queryset = ContactRole.objects.all()
    form = ContactRoleForm


@register_model_view(model=ContactRole, name="delete")
class ContactRoleDelete(ObjectDeleteView):
    permission_required = "messaging.delete_contactrole"
    queryset = ContactRole.objects.all()


@register_model_view(model=ContactRole, name="bulk_edit", path="edit", detail=False)
class ContactRoleBulkEdit(BulkEditView):
    permission_required = "messaging.change_contactrole"
    queryset = ContactRole.objects.all()
    filterset = ContactRoleFilterSet
    table = ContactRoleTable
    form = ContactRoleBulkEditForm


@register_model_view(model=ContactRole, name="bulk_delete", path="delete", detail=False)
class ContactRoleBulkDelete(BulkDeleteView):
    queryset = ContactRole.objects.all()
    filterset = ContactRoleFilterSet
    table = ContactRoleTable
