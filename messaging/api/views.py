from rest_framework.routers import APIRootView

from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ..filtersets import (
    ContactAssignmentFilterSet,
    ContactFilterSet,
    ContactRoleFilterSet,
    EmailFilterSet,
)
from ..models import Contact, ContactAssignment, ContactRole, Email
from .serializers import (
    ContactAssignmentSerializer,
    ContactRoleSerializer,
    ContactSerializer,
    EmailSerializer,
)


class MessagingRootView(APIRootView):
    def get_view_name(self):
        return "Messaging"


class ContactRoleViewSet(PeeringManagerModelViewSet):
    queryset = ContactRole.objects.all()
    serializer_class = ContactRoleSerializer
    filterset_class = ContactRoleFilterSet


class ContactViewSet(PeeringManagerModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilterSet


class ContactAssignmentViewSet(PeeringManagerModelViewSet):
    queryset = ContactAssignment.objects.prefetch_related("object", "contact", "role")
    serializer_class = ContactAssignmentSerializer
    filterset_class = ContactAssignmentFilterSet


class EmailViewSet(PeeringManagerModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    filterset_class = EmailFilterSet
