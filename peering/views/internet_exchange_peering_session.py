from extras.views import ObjectConfigContextView
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ImportFromObjectView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import InternetExchangePeeringSessionFilterSet
from ..forms import (
    InternetExchangePeeringSessionBulkEditForm,
    InternetExchangePeeringSessionFilterForm,
    InternetExchangePeeringSessionForm,
)
from ..models import (
    AutonomousSystem,
    InternetExchange,
    InternetExchangePeeringSession,
    NetworkIXLan,
)
from ..tables import InternetExchangePeeringSessionTable

__all__ = (
    "InternetExchangePeeringSessionBulkDelete",
    "InternetExchangePeeringSessionBulkEdit",
    "InternetExchangePeeringSessionConfigContext",
    "InternetExchangePeeringSessionDelete",
    "InternetExchangePeeringSessionEdit",
    "InternetExchangePeeringSessionImportFromPeeringDB",
    "InternetExchangePeeringSessionList",
    "InternetExchangePeeringSessionView",
)


@register_model_view(InternetExchangePeeringSession, name="list", path="", detail=False)
class InternetExchangePeeringSessionList(ObjectListView):
    permission_required = "peering.view_internetexchangepeeringsession"
    queryset = (
        InternetExchangePeeringSession.objects.order_by(
            "autonomous_system", "ip_address"
        )
        .select_related("autonomous_system")
        .defer("autonomous_system__prefixes", "autonomous_system__as_list")
    )
    table = InternetExchangePeeringSessionTable
    filterset = InternetExchangePeeringSessionFilterSet
    filterset_form = InternetExchangePeeringSessionFilterForm
    template_name = "peering/internetexchangepeeringsession/list.html"


@register_model_view(InternetExchangePeeringSession)
class InternetExchangePeeringSessionView(ObjectView):
    permission_required = "peering.view_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()


@register_model_view(model=InternetExchangePeeringSession, name="add", detail=False)
@register_model_view(model=InternetExchangePeeringSession, name="edit")
class InternetExchangePeeringSessionEdit(ObjectEditView):
    queryset = InternetExchangePeeringSession.objects.all()
    form = InternetExchangePeeringSessionForm


@register_model_view(InternetExchangePeeringSession, name="delete")
class InternetExchangePeeringSessionDelete(ObjectDeleteView):
    permission_required = "peering.delete_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()


@register_model_view(
    InternetExchangePeeringSession, name="bulk_edit", path="edit", detail=False
)
class InternetExchangePeeringSessionBulkEdit(BulkEditView):
    permission_required = "peering.change_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.select_related(
        "autonomous_system"
    ).defer("autonomous_system__prefixes", "autonomous_system__as_list")
    filterset = InternetExchangePeeringSessionFilterSet
    table = InternetExchangePeeringSessionTable
    form = InternetExchangePeeringSessionBulkEditForm


@register_model_view(
    InternetExchangePeeringSession, name="bulk_delete", path="delete", detail=False
)
class InternetExchangePeeringSessionBulkDelete(BulkDeleteView):
    queryset = InternetExchangePeeringSession.objects.all()
    filterset = InternetExchangePeeringSessionFilterSet
    table = InternetExchangePeeringSessionTable


@register_model_view(
    InternetExchangePeeringSession, name="configcontext", path="config-context"
)
class InternetExchangePeeringSessionConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()
    base_template = "peering/internetexchangepeeringsession/_base.html"


@register_model_view(
    InternetExchangePeeringSession, name="add_from_peeringdb", detail=False
)
class InternetExchangePeeringSessionImportFromPeeringDB(ImportFromObjectView):
    permission_required = "peering.add_internetexchangepeeringsession"
    queryset = NetworkIXLan.objects.all()
    form_model = InternetExchangePeeringSessionForm
    template_name = "peering/internetexchangepeeringsession/add_from_peeringdb.html"

    def process_base_object(self, request, base):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            return []

        ixp = None
        if "internet_exchange_id" in request.POST:
            ixp = InternetExchange.objects.get(
                pk=request.POST.get("internet_exchange_id")
            )

        return InternetExchangePeeringSession.create_from_peeringdb(
            affiliated, ixp, base
        )

    def sort_objects(self, object_list):
        objects = []
        for object_couple in object_list:
            for o in object_couple:
                if o:
                    objects.append(
                        {
                            "autonomous_system": o.autonomous_system,
                            "ixp_connection": o.ixp_connection,
                            "ip_address": o.ip_address,
                        }
                    )
        return objects
