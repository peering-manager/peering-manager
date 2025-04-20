from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import TagFilterSet
from ..forms import TagBulkEditForm, TagFilterForm, TagForm
from ..models import Tag, TaggedItem
from ..tables import TaggedItemTable, TagTable

__all__ = ("TagBulkDelete", "TagBulkEdit", "TagDelete", "TagEdit", "TagList", "TagView")


@register_model_view(Tag, name="list", path="", detail=False)
class TagList(ObjectListView):
    permission_required = "extras.view_tag"
    queryset = Tag.objects.annotate(
        items=Count("extras_taggeditem_items", distinct=True)
    ).order_by("name")
    filterset = TagFilterSet
    filterset_form = TagFilterForm
    table = TagTable
    template_name = "extras/tag/list.html"


@register_model_view(Tag)
class TagView(ObjectView):
    permission_required = "extras.view_tag"
    queryset = Tag.objects.all()

    def get_extra_context(self, request, instance):
        tagged_items = TaggedItem.objects.filter(tag=instance)
        taggeditem_table = TaggedItemTable(data=tagged_items, orderable=False)
        taggeditem_table.configure(request)

        object_types = [
            {
                "content_type": ContentType.objects.get(pk=ti["content_type"]),
                "item_count": ti["item_count"],
            }
            for ti in tagged_items.values("content_type").annotate(
                item_count=Count("pk")
            )
        ]

        return {
            "taggeditem_table": taggeditem_table,
            "tagged_item_count": tagged_items.count(),
            "object_types": object_types,
        }


@register_model_view(model=Tag, name="add", detail=False)
@register_model_view(model=Tag, name="edit")
class TagEdit(ObjectEditView):
    queryset = Tag.objects.all()
    form = TagForm


@register_model_view(model=Tag, name="delete")
class TagDelete(ObjectDeleteView):
    permission_required = "extras.delete_tag"
    queryset = Tag.objects.all()


@register_model_view(model=Tag, name="bulk_edit", path="edit", detail=False)
class TagBulkEdit(BulkEditView):
    permission_required = "extras.change_tag"
    queryset = Tag.objects.annotate(
        items=Count("extras_taggeditem_items", distinct=True)
    ).order_by("name")
    filterset = TagFilterSet
    table = TagTable
    form = TagBulkEditForm


@register_model_view(model=Tag, name="bulk_delete", path="delete", detail=False)
class TagBulkDelete(BulkDeleteView):
    permission_required = "extras.delete_tag"
    queryset = Tag.objects.annotate(
        items=Count("extras_taggeditem_items", distinct=True)
    ).order_by("name")
    filterset = TagFilterSet
    table = TagTable
