from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from peering_manager.views.generic import ObjectListView, PermissionRequiredMixin
from utils.functions import shallow_compare_dict
from utils.views import register_model_view

from ..enums import ObjectChangeAction
from ..filtersets import ObjectChangeFilterSet
from ..forms import ObjectChangeFilterForm
from ..models import ObjectChange
from ..tables import ObjectChangeTable

__all__ = ("ObjectChangeList", "ObjectChangeView")


@register_model_view(ObjectChange, name="list", path="", detail=False)
class ObjectChangeList(ObjectListView):
    permission_required = "core.view_objectchange"
    queryset = ObjectChange.objects.select_related("user").prefetch_related(
        "changed_object"
    )
    filterset = ObjectChangeFilterSet
    filterset_form = ObjectChangeFilterForm
    table = ObjectChangeTable
    template_name = "core/object_change/list.html"


@register_model_view(ObjectChange)
class ObjectChangeView(PermissionRequiredMixin, View):
    permission_required = "core.view_objectchange"

    def get(self, request, pk):
        instance = get_object_or_404(ObjectChange, pk=pk)

        related_changes = ObjectChange.objects.filter(
            request_id=instance.request_id
        ).exclude(pk=instance.pk)
        related_changes_table = ObjectChangeTable(
            data=related_changes[:50], orderable=False
        )

        object_changes = ObjectChange.objects.filter(
            changed_object_type=instance.changed_object_type,
            changed_object_id=instance.changed_object_id,
        )

        next_change = (
            object_changes.filter(time__gt=instance.time).order_by("time").first()
        )
        previous_change = (
            object_changes.filter(time__lt=instance.time).order_by("-time").first()
        )

        if (
            not instance.prechange_data
            and instance.action
            in [ObjectChangeAction.UPDATE, ObjectChangeAction.DELETE]
            and previous_change
        ):
            non_atomic_change = True
            prechange_data = previous_change.postchange_data
        else:
            non_atomic_change = False
            prechange_data = instance.prechange_data

        if prechange_data and instance.postchange_data:
            diff_added = shallow_compare_dict(
                prechange_data or {},
                instance.postchange_data or {},
                exclude=["updated"],
            )
            diff_removed = (
                {x: prechange_data.get(x) for x in diff_added} if prechange_data else {}
            )
        else:
            diff_added = None
            diff_removed = None

        return render(
            request,
            "core/object_change/details.html",
            {
                "instance": instance,
                "diff_added": diff_added,
                "diff_removed": diff_removed,
                "next_change": next_change,
                "previous_change": previous_change,
                "related_changes_table": related_changes_table,
                "related_changes_count": related_changes.count(),
                "non_atomic_change": non_atomic_change,
            },
        )
