from django.shortcuts import get_object_or_404

from bgp.filters import RelationshipFilterSet
from bgp.forms import RelationshipFilterForm, RelationshipForm
from bgp.models import Relationship
from bgp.tables import RelationshipTable
from utils.views import (
    AddOrEditView,
    BulkDeleteView,
    DeleteView,
    DetailsView,
    ModelListView,
    PermissionRequiredMixin,
)


class RelationshipList(PermissionRequiredMixin, ModelListView):
    permission_required = "bgp.view_relationship"
    queryset = Relationship.objects.all()
    filter = RelationshipFilterSet
    filter_form = RelationshipFilterForm
    table = RelationshipTable
    template = "bgp/relationship/list.html"


class RelationshipDetails(DetailsView):
    permission_required = "bgp.view_relationship"
    queryset = Relationship.objects.all()

    def get_context(self, request, **kwargs):
        return {
            "instance": get_object_or_404(self.queryset, **kwargs),
            "active_tab": "main",
        }


class RelationshipAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "bgp.add_relationship"
    model = Relationship
    form = RelationshipForm
    return_url = "bgp:relationship_list"
    template = "bgp/relationship/add_edit.html"


class RelationshipEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "bgp.change_relationship"
    model = Relationship
    form = RelationshipForm
    template = "bgp/relationship/add_edit.html"


class RelationshipDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "bgp.delete_relationship"
    model = Relationship
    return_url = "bgp:relationship_list"


class RelationshipBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "bgp.delete_relationship"
    model = Relationship
    filter = RelationshipFilterSet
    table = RelationshipTable
