from django.db.models import Count

from extras.views import ObjectConfigContextView
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import ViewTab, register_model_view

from ..filtersets import BGPGroupFilterSet, DirectPeeringSessionFilterSet
from ..forms import (
    BGPGroupBulkEditForm,
    BGPGroupFilterForm,
    BGPGroupForm,
    DirectPeeringSessionFilterForm,
)
from ..models import BGPGroup, DirectPeeringSession
from ..tables import BGPGroupTable, DirectPeeringSessionTable

__all__ = (
    "BGPGroupBulkDelete",
    "BGPGroupBulkEdit",
    "BGPGroupConfigContext",
    "BGPGroupDelete",
    "BGPGroupEdit",
    "BGPGroupList",
    "BGPGroupPeeringSessions",
    "BGPGroupView",
)


@register_model_view(BGPGroup, name="list", path="", detail=False)
class BGPGroupList(ObjectListView):
    permission_required = "peering.view_bgpgroup"
    queryset = BGPGroup.objects.annotate(
        directpeeringsession_count=Count("directpeeringsession")
    ).order_by("name", "slug")
    filterset = BGPGroupFilterSet
    filterset_form = BGPGroupFilterForm
    table = BGPGroupTable
    template_name = "peering/bgpgroup/list.html"


@register_model_view(BGPGroup)
class BGPGroupView(ObjectView):
    permission_required = "peering.view_bgpgroup"
    queryset = BGPGroup.objects.all()


@register_model_view(model=BGPGroup, name="add", detail=False)
@register_model_view(model=BGPGroup, name="edit")
class BGPGroupEdit(ObjectEditView):
    queryset = BGPGroup.objects.all()
    form = BGPGroupForm


@register_model_view(BGPGroup, name="delete")
class BGPGroupDelete(ObjectDeleteView):
    permission_required = "peering.delete_bgpgroup"
    queryset = BGPGroup.objects.all()


@register_model_view(BGPGroup, name="bulk_edit", path="edit", detail=False)
class BGPGroupBulkEdit(BulkEditView):
    permission_required = "peering.change_bgpgroup"
    queryset = BGPGroup.objects.all()
    filterset = BGPGroupFilterSet
    table = BGPGroupTable
    form = BGPGroupBulkEditForm


@register_model_view(BGPGroup, name="bulk_delete", path="delete", detail=False)
class BGPGroupBulkDelete(BulkDeleteView):
    queryset = BGPGroup.objects.all()
    filterset = BGPGroupFilterSet
    table = BGPGroupTable


@register_model_view(BGPGroup, name="configcontext", path="config-context")
class BGPGroupConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_bgpgroup"
    queryset = BGPGroup.objects.all()
    base_template = "peering/bgpgroup/_base.html"


@register_model_view(BGPGroup, name="peering_sessions", path="peering-sessions")
class BGPGroupPeeringSessions(ObjectChildrenView):
    permission_required = ("peering.view_bgpgroup", "peering.view_directpeeringsession")
    queryset = BGPGroup.objects.all()
    child_model = DirectPeeringSession
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template_name = "peering/bgpgroup/sessions.html"
    tab = ViewTab(
        label="Direct Peering Sessions",
        badge=lambda instance: instance.get_peering_sessions().count(),
        permission="peering.view_directpeeringsession",
    )

    def get_children(self, request, parent):
        return parent.directpeeringsession_set.prefetch_related(
            "autonomous_system", "router"
        ).order_by("autonomous_system", "ip_address")
