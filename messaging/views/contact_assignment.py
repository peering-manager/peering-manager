from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from peering_manager.views.generic import ObjectDeleteView, ObjectEditView
from utils.views import register_model_view

from ..forms import ContactAssignmentForm
from ..models import ContactAssignment

__all__ = ("ContactAssignmentDeleteView", "ContactAssignmentEditView")


@register_model_view(model=ContactAssignment, name="add", detail=False)
@register_model_view(model=ContactAssignment, name="edit")
class ContactAssignmentEditView(ObjectEditView):
    permission_required = "messaging.change_contactassignment"
    queryset = ContactAssignment.objects.all()
    form = ContactAssignmentForm
    template_name = "messaging/contactassignment/edit.html"

    def alter_object(self, instance, request, args, kwargs):
        if not instance.pk:
            content_type = get_object_or_404(
                ContentType, pk=request.GET.get("content_type")
            )
            instance.object = get_object_or_404(
                content_type.model_class(), pk=request.GET.get("object_id")
            )
        return instance


@register_model_view(model=ContactAssignment, name="delete")
class ContactAssignmentDeleteView(ObjectDeleteView):
    permission_required = "messaging.delete_contactassignment"
    queryset = ContactAssignment.objects.all()
