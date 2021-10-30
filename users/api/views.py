from django.contrib.auth.models import Group, User
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from peering.models import AutonomousSystem
from peering_manager.api.views import ModelViewSet
from users.filters import GroupFilterSet, UserFilterSet

from .serializers import GroupSerializer, UserSerializer


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all().annotate(user_count=Count("user")).order_by("name")
    serializer_class = GroupSerializer
    filterset_class = GroupFilterSet


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().prefetch_related("groups").order_by("username")
    serializer_class = UserSerializer
    filterset_class = UserFilterSet

    @action(detail=True, methods=["patch"], url_path="set-context-as")
    def set_context_as(self, request, pk=None):
        preferences = self.get_object().preferences
        try:
            autonomous_system = AutonomousSystem.objects.get(
                pk=int(request.data["as_id"]), affiliated=True
            )
            preferences.set("context.as", autonomous_system.pk, commit=True)
        except AutonomousSystem.DoesNotExist:
            return Response(
                {
                    "error": f"affiliated autonomous system with id {request.data['as_id']} not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"status": "success"})
