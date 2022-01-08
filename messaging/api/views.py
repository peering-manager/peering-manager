from rest_framework.routers import APIRootView

from messaging.api.serializers import (
    ContactAssignmentSerializer,
    ContactRoleSerializer,
    ContactSerializer,
    EmailSerializer,
)
from messaging.filters import (
    ContactAssignmentFilterSet,
    ContactFilterSet,
    ContactRoleFilterSet,
    EmailFilterSet,
)
from messaging.models import Contact, ContactAssignment, ContactRole, Email
from peering_manager.api.views import ModelViewSet


class MessagingRootView(APIRootView):
    def get_view_name(self):
        return "Messaging"


class ContactRoleViewSet(ModelViewSet):
    queryset = ContactRole.objects.all()
    serializer_class = ContactRoleSerializer
    filterset_class = ContactRoleFilterSet


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilterSet


class ContactAssignmentViewSet(ModelViewSet):
    queryset = ContactAssignment.objects.prefetch_related("object", "contact", "role")
    serializer_class = ContactAssignmentSerializer
    filterset_class = ContactAssignmentFilterSet


class EmailViewSet(ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    filterset_class = EmailFilterSet
