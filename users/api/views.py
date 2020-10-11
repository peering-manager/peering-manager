from django.contrib.auth.models import Group, User
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import APIRootView

from .serializers import GroupSerializer, UserSerializer
from peering.models import AutonomousSystem
from users.filters import GroupFilterSet, UserFilterSet
from utils.api import ModelViewSet


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all().annotate(user_count=Count("user")).order_by("name")
    serializer_class = GroupSerializer
    filterset_class = GroupFilterSet


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().prefetch_related("groups").order_by("username")
    serializer_class = UserSerializer
    filterset_class = UserFilterSet

    @action(detail=True, methods=["patch"], url_path="set-context-asn")
    def set_context_asn(self, request, pk=None):
        preferences = self.get_object().preferences
        try:
            autonomous_system = AutonomousSystem.objects.get(
                asn=int(request.data["asn"]), affiliated=True
            )
            preferences.set("context.asn", autonomous_system.pk, commit=True)
        except AutonomousSystem.DoesNotExist:
            return Response(
                {
                    "error": f"affiliated autonomous system with asn {request.data['asn']} not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"status": "success"})
