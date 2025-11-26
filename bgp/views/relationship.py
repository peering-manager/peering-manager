from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import RelationshipFilterSet
from ..forms import RelationshipFilterForm, RelationshipForm
from ..models import Relationship
from ..tables import RelationshipTable

__all__ = (
    "RelationshipBulkDelete",
    "RelationshipDelete",
    "RelationshipEdit",
    "RelationshipList",
    "RelationshipView",
)


@register_model_view(model=Relationship, name="list", path="", detail=False)
class RelationshipList(ObjectListView):
    permission_required = "bgp.view_relationship"
    queryset = Relationship.objects.all()
    filterset = RelationshipFilterSet
    filterset_form = RelationshipFilterForm
    table = RelationshipTable
    template_name = "bgp/relationship/list.html"


@register_model_view(model=Relationship)
class RelationshipView(ObjectView):
    permission_required = "bgp.view_relationship"
    queryset = Relationship.objects.all()


@register_model_view(model=Relationship, name="add", detail=False)
@register_model_view(model=Relationship, name="edit")
class RelationshipEdit(ObjectEditView):
    queryset = Relationship.objects.all()
    form = RelationshipForm


@register_model_view(model=Relationship, name="delete")
class RelationshipDelete(ObjectDeleteView):
    permission_required = "bgp.delete_relationship"
    queryset = Relationship.objects.all()


@register_model_view(
    model=Relationship, name="bulk_delete", path="delete", detail=False
)
class RelationshipBulkDelete(BulkDeleteView):
    queryset = Relationship.objects.all()
    filterset = RelationshipFilterSet
    table = RelationshipTable
