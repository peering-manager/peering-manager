from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from peering_manager.views.generic import ObjectDeleteView, ObjectEditView
from utils.views import register_model_view

from ..forms import ConfigContextAssignmentForm
from ..models import ConfigContextAssignment

__all__ = ("ConfigContextAssignmentDeleteView", "ConfigContextAssignmentEditView")


@register_model_view(ConfigContextAssignment, name="add", detail=False)
@register_model_view(ConfigContextAssignment, name="edit")
class ConfigContextAssignmentEditView(ObjectEditView):
    permission_required = "extras.edit_configcontextassignment"
    queryset = ConfigContextAssignment.objects.all()
    form = ConfigContextAssignmentForm
    template_name = "extras/configcontextassignment/edit.html"

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            content_type = get_object_or_404(
                ContentType, pk=request.GET.get("content_type")
            )
            instance.object = get_object_or_404(
                content_type.model_class(), pk=request.GET.get("object_id")
            )
        return instance


@register_model_view(ConfigContextAssignment, name="delete")
class ConfigContextAssignmentDeleteView(ObjectDeleteView):
    permission_required = "extras.delete_configcontextassignment"
    queryset = ConfigContextAssignment.objects.all()
