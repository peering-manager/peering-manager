from bgp.filters import RelationshipFilterSet
from bgp.forms import RelationshipFilterForm, RelationshipForm
from bgp.models import Relationship
from bgp.tables import RelationshipTable
from peering_manager.views.generics import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)


class RelationshipList(ObjectListView):
    permission_required = "bgp.view_relationship"
    queryset = Relationship.objects.all()
    filterset = RelationshipFilterSet
    filterset_form = RelationshipFilterForm
    table = RelationshipTable
    template_name = "bgp/relationship/list.html"


class RelationshipView(ObjectView):
    permission_required = "bgp.view_relationship"
    queryset = Relationship.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class RelationshipAdd(ObjectEditView):
    permission_required = "bgp.add_relationship"
    queryset = Relationship.objects.all()
    model_form = RelationshipForm
    template_name = "bgp/relationship/add_edit.html"


class RelationshipEdit(ObjectEditView):
    permission_required = "bgp.change_relationship"
    queryset = Relationship.objects.all()
    model_form = RelationshipForm
    template_name = "bgp/relationship/add_edit.html"


class RelationshipDelete(ObjectDeleteView):
    permission_required = "bgp.delete_relationship"
    queryset = Relationship.objects.all()


class RelationshipBulkDelete(BulkDeleteView):
    permission_required = "bgp.delete_relationship"
    queryset = Relationship.objects.all()
    filterset = RelationshipFilterSet
    table = RelationshipTable
