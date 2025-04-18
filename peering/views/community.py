from extras.views import ObjectConfigContextView
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import CommunityFilterSet
from ..forms import CommunityBulkEditForm, CommunityFilterForm, CommunityForm
from ..models import Community
from ..tables import CommunityTable

__all__ = (
    "CommunityBulkDelete",
    "CommunityBulkEdit",
    "CommunityConfigContext",
    "CommunityDelete",
    "CommunityEdit",
    "CommunityList",
    "CommunityView",
)


@register_model_view(Community, name="list", path="", detail=False)
class CommunityList(ObjectListView):
    permission_required = "peering.view_community"
    queryset = Community.objects.all()
    filterset = CommunityFilterSet
    filterset_form = CommunityFilterForm
    table = CommunityTable
    template_name = "peering/community/list.html"


@register_model_view(Community)
class CommunityView(ObjectView):
    permission_required = "peering.view_community"
    queryset = Community.objects.all()
    tab = "main"


@register_model_view(model=Community, name="add", detail=False)
@register_model_view(model=Community, name="edit")
class CommunityEdit(ObjectEditView):
    queryset = Community.objects.all()
    form = CommunityForm


@register_model_view(Community, name="delete")
class CommunityDelete(ObjectDeleteView):
    permission_required = "peering.delete_community"
    queryset = Community.objects.all()


@register_model_view(Community, name="bulk_edit", path="edit", detail=False)
class CommunityBulkEdit(BulkEditView):
    permission_required = "peering.change_community"
    queryset = Community.objects.all()
    filterset = CommunityFilterSet
    table = CommunityTable
    form = CommunityBulkEditForm


@register_model_view(Community, name="bulk_delete", path="delete", detail=False)
class CommunityBulkDelete(BulkDeleteView):
    queryset = Community.objects.all()
    filterset = CommunityFilterSet
    table = CommunityTable


@register_model_view(Community, name="configcontext", path="config-context")
class CommunityConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_community"
    queryset = Community.objects.all()
    base_template = "peering/community/_base.html"
