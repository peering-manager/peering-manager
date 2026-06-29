from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import ViewTab, register_model_view

from ..enums import RequestedSessionStatus
from ..filtersets import PeeringRequestFilterSet, RequestedSessionFilterSet
from ..forms import PeeringRequestFilterForm, PeeringRequestForm
from ..models import AutonomousSystem, PeeringRequest, RequestedSession
from ..tables import PeeringRequestTable, RequestedSessionTable
from .mixins import AffiliatedAutonomousSystemMixin

__all__ = (
    "PeeringRequestBulkDelete",
    "PeeringRequestDelete",
    "PeeringRequestEdit",
    "PeeringRequestList",
    "PeeringRequestRequestedSessions",
    "PeeringRequestView",
)


@register_model_view(PeeringRequest, name="list", path="", detail=False)
class PeeringRequestList(ObjectListView):
    permission_required = "peering.view_peeringrequest"
    queryset = PeeringRequest.objects.select_related("local_autonomous_system").all()
    filterset = PeeringRequestFilterSet
    filterset_form = PeeringRequestFilterForm
    table = PeeringRequestTable
    template_name = "peering/peeringrequest/list.html"


@register_model_view(PeeringRequest)
class PeeringRequestView(ObjectView):
    permission_required = "peering.view_peeringrequest"
    queryset = PeeringRequest.objects.all()

    def get_extra_context(self, request, instance):
        try:
            requesting_as = AutonomousSystem.objects.get(asn=instance.requesting_asn)
        except AutonomousSystem.DoesNotExist:
            requesting_as = None

        return {
            "requesting_autonomous_system": requesting_as,
            "requested_sessions": instance.requested_sessions.all(),
            "pending_sessions": instance.requested_sessions.filter(
                status=RequestedSessionStatus.PENDING
            ).select_related("ixp_connection__internet_exchange_point"),
        }


@register_model_view(model=PeeringRequest, name="add", detail=False)
@register_model_view(model=PeeringRequest, name="edit")
class PeeringRequestEdit(AffiliatedAutonomousSystemMixin, ObjectEditView):
    queryset = PeeringRequest.objects.all()
    form = PeeringRequestForm


@register_model_view(PeeringRequest, name="delete")
class PeeringRequestDelete(ObjectDeleteView):
    permission_required = "peering.delete_peeringrequest"
    queryset = PeeringRequest.objects.all()


@register_model_view(PeeringRequest, name="bulk_delete", path="delete", detail=False)
class PeeringRequestBulkDelete(BulkDeleteView):
    queryset = PeeringRequest.objects.all()
    filterset = PeeringRequestFilterSet
    table = PeeringRequestTable


@register_model_view(PeeringRequest, name="requested_sessions", path="requested-sessions")
class PeeringRequestRequestedSessions(ObjectChildrenView):
    permission_required = (
        "peering.view_peeringrequest",
        "peering.view_requestedsession",
    )
    queryset = PeeringRequest.objects.all()
    child_model = RequestedSession
    filterset = RequestedSessionFilterSet
    table = RequestedSessionTable
    template_name = "peering/peeringrequest/requested_sessions.html"
    tab = ViewTab(
        label="Requested Sessions",
        badge=lambda instance: instance.requested_sessions.count(),
        permission="peering.view_requestedsession",
    )

    def get_children(self, request, parent):
        return parent.requested_sessions.select_related("ixp_connection__internet_exchange_point").all()
