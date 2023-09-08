from django.contrib.auth.models import Group, User
from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.viewsets import ViewSet

from peering_manager.api.viewsets import PeeringManagerModelViewSet
from utils.functions import merge_hash

from ..filtersets import GroupFilterSet, UserFilterSet
from ..models import UserPreferences
from .serializers import GroupSerializer, UserSerializer


class UsersRootView(APIRootView):
    def get_view_name(self):
        return "Users"


class GroupViewSet(PeeringManagerModelViewSet):
    queryset = Group.objects.all().annotate(user_count=Count("user")).order_by("name")
    serializer_class = GroupSerializer
    filterset_class = GroupFilterSet


class UserViewSet(PeeringManagerModelViewSet):
    queryset = User.objects.all().prefetch_related("groups").order_by("username")
    serializer_class = UserSerializer
    filterset_class = UserFilterSet


class UserPreferencesViewSet(ViewSet):
    """
    An API endpoint via which a user can update his or her own UserPreferences data
    (but no one else's).
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPreferences.objects.filter(user=self.request.user)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def list(self, request):
        """
        Return the UserPreferences for the currently authenticated User.
        """
        userpref = self.get_queryset().first()
        return Response(userpref.data)

    @extend_schema(methods=["patch"], responses={201: OpenApiTypes.OBJECT})
    def patch(self, request):
        """
        Update the UserPreferences for the currently authenticated User.
        """
        # TODO: How can we validate this data?
        userpref = self.get_queryset().first()
        userpref.data = merge_hash(userpref.data, request.data)
        userpref.save()
        return Response(userpref.data)
