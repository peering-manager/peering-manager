from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)

from .filtersets import RelationshipFilterSet
from .forms import RelationshipFilterForm, RelationshipForm
from .models import Relationship
from .tables import RelationshipTable


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
    tab = "main"


class RelationshipEdit(ObjectEditView):
    queryset = Relationship.objects.all()
    form = RelationshipForm


class RelationshipDelete(ObjectDeleteView):
    permission_required = "bgp.delete_relationship"
    queryset = Relationship.objects.all()


class RelationshipBulkDelete(BulkDeleteView):
    queryset = Relationship.objects.all()
    filterset = RelationshipFilterSet
    table = RelationshipTable
