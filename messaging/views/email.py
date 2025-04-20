from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import EmailFilterSet
from ..forms import EmailFilterForm, EmailForm
from ..models import Email
from ..tables import EmailTable


@register_model_view(model=Email, name="list", path="", detail=False)
class EmailList(ObjectListView):
    permission_required = "messaging.view_email"
    queryset = Email.objects.all()
    filterset = EmailFilterSet
    filterset_form = EmailFilterForm
    table = EmailTable
    template_name = "messaging/email/list.html"


@register_model_view(model=Email)
class EmailView(ObjectView):
    permission_required = "messaging.view_email"
    queryset = Email.objects.all()


@register_model_view(model=Email, name="add", detail=False)
@register_model_view(model=Email, name="edit")
class EmailEdit(ObjectEditView):
    queryset = Email.objects.all()
    form = EmailForm


@register_model_view(model=Email, name="delete")
class EmailDelete(ObjectDeleteView):
    permission_required = "messaging.delete_email"
    queryset = Email.objects.all()


@register_model_view(model=Email, name="bulk_delete", path="delete", detail=False)
class EmailBulkDelete(BulkDeleteView):
    queryset = Email.objects.all()
    filterset = EmailFilterSet
    table = EmailTable
