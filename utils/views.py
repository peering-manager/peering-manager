import sys

from django import template
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME
from django.views.generic import View
from django_tables2 import RequestConfig

from peering_manager.views.generics import ObjectListView, PermissionRequiredMixin

from .filters import ObjectChangeFilterSet
from .forms import ObjectChangeFilterForm
from .functions import shallow_compare_dict
from .models import ObjectChange
from .paginators import EnhancedPaginator, get_paginate_count
from .tables import ObjectChangeTable


class ObjectChangeList(ObjectListView):
    permission_required = "utils.view_objectchange"
    queryset = ObjectChange.objects.select_related("user").prefetch_related(
        "changed_object"
    )
    filterset = ObjectChangeFilterSet
    filterset_form = ObjectChangeFilterForm
    table = ObjectChangeTable
    template_name = "utils/object_change/list.html"


class ObjectChangeLog(View):
    def get(self, request, model, **kwargs):
        # Get object by model and kwargs (like asn=64500)
        obj = get_object_or_404(model, **kwargs)

        # Gather all changes for this object (and its related objects)
        content_type = ContentType.objects.get_for_model(model)
        objectchanges = ObjectChange.objects.select_related(
            "user", "changed_object_type"
        ).filter(
            Q(changed_object_type=content_type, changed_object_id=obj.pk)
            | Q(related_object_type=content_type, related_object_id=obj.pk)
        )
        objectchanges_table = ObjectChangeTable(data=objectchanges, orderable=False)

        # Apply the request context
        paginate = {
            "paginator_class": EnhancedPaginator,
            "per_page": get_paginate_count(request),
        }
        RequestConfig(request, paginate).configure(objectchanges_table)

        # Check whether a header template exists for this model
        base_template = f"{model._meta.app_label}/{model._meta.model_name}/_base.html"
        try:
            template.loader.get_template(base_template)
        except template.TemplateDoesNotExist:
            base_template = "_base.html"

        return render(
            request,
            "utils/object_change/log.html",
            {
                "instance": obj,
                "table": objectchanges_table,
                "base_template": base_template,
                "active_tab": "changelog",
            },
        )


class ObjectChangeView(PermissionRequiredMixin, View):
    permission_required = "utils.view_objectchange"

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
            and instance.action in ["update", "delete"]
            and previous_change
        ):
            non_atomic_change = True
            prechange_data = previous_change.postchange_data
        else:
            non_atomic_change = False
            prechange_data = instance.prechange_data

        if prechange_data and instance.postchange_data:
            diff_added = shallow_compare_dict(
                prechange_data or dict(),
                instance.postchange_data or dict(),
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
            "utils/object_change/details.html",
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


@requires_csrf_token
def ServerError(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    Custom 500 handler to provide details when rendering 500.html.
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )
    type_, error, _ = sys.exc_info()

    return HttpResponseServerError(
        template.render({"exception": str(type_), "error": error})
    )
