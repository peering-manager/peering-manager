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

from ..filtersets import RoutingPolicyFilterSet
from ..forms import (
    RoutingPolicyBulkEditForm,
    RoutingPolicyFilterForm,
    RoutingPolicyForm,
)
from ..models import RoutingPolicy
from ..tables import RoutingPolicyTable

__all__ = (
    "RoutingPolicyBulkDelete",
    "RoutingPolicyBulkEdit",
    "RoutingPolicyConfigContext",
    "RoutingPolicyDelete",
    "RoutingPolicyEdit",
    "RoutingPolicyList",
    "RoutingPolicyView",
)


@register_model_view(RoutingPolicy, name="list", path="", detail=False)
class RoutingPolicyList(ObjectListView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    filterset_form = RoutingPolicyFilterForm
    table = RoutingPolicyTable
    template_name = "peering/routingpolicy/list.html"


@register_model_view(RoutingPolicy)
class RoutingPolicyView(ObjectView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()


@register_model_view(model=RoutingPolicy, name="add", detail=False)
@register_model_view(model=RoutingPolicy, name="edit")
class RoutingPolicyEdit(ObjectEditView):
    queryset = RoutingPolicy.objects.all()
    form = RoutingPolicyForm


@register_model_view(RoutingPolicy, name="delete")
class RoutingPolicyDelete(ObjectDeleteView):
    permission_required = "peering.delete_routingpolicy"
    queryset = RoutingPolicy.objects.all()


@register_model_view(RoutingPolicy, name="bulk_edit", path="edit", detail=False)
class RoutingPolicyBulkEdit(BulkEditView):
    permission_required = "peering.change_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    table = RoutingPolicyTable
    form = RoutingPolicyBulkEditForm


@register_model_view(RoutingPolicy, name="bulk_delete", path="delete", detail=False)
class RoutingPolicyBulkDelete(BulkDeleteView):
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    table = RoutingPolicyTable


@register_model_view(RoutingPolicy, name="configcontext", path="config-context")
class RoutingPolicyConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    base_template = "peering/routingpolicy/_base.html"
