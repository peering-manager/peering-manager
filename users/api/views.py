from django.contrib.auth.models import Group, User
from django.db.models import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.viewsets import ViewSet

from peering_manager.api.viewsets import PeeringManagerModelViewSet
from utils.functions import merge_hash

from ..filtersets import (
    GroupFilterSet,
    TokenObjectPermissionFilterSet,
    UserFilterSet,
)
from ..models import TokenObjectPermission, UserPreferences
from .serializers import (
    GroupSerializer,
    TokenObjectPermissionSerializer,
    UserSerializer,
)


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


class TokenObjectPermissionViewSet(PeeringManagerModelViewSet):
    """
    API endpoint for managing token object permissions.

    Access is restricted based on the token's can_manage_permissions flag:
    - If False (default): Can only view their own token's permissions
    - If True: Can view/create/update/delete all token permissions
    """

    queryset = TokenObjectPermission.objects.select_related(
        "token", "token__user", "content_type"
    ).order_by("-created")
    serializer_class = TokenObjectPermissionSerializer
    filterset_class = TokenObjectPermissionFilterSet

    def get_queryset(self):
        """Filter queryset based on token's can_manage_permissions flag."""
        queryset = super().get_queryset()

        # If using token authentication
        if hasattr(self.request, "auth") and self.request.auth:
            token = self.request.auth

            # If token doesn't have permission management flag, only show their own permissions
            if not token.can_manage_permissions:
                queryset = queryset.filter(token=token)

        return queryset

    def check_permissions(self, request):
        """Check if token has permission to perform this action."""
        super().check_permissions(request)

        # If using token authentication
        if hasattr(request, "auth") and request.auth:
            token = request.auth

            # Only allow GET (list/retrieve) if token doesn't have can_manage_permissions
            if not token.can_manage_permissions and request.method not in [
                "GET",
                "HEAD",
                "OPTIONS",
            ]:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "This token does not have permission to manage token permissions. "
                    "Set can_manage_permissions=True on the token to enable this."
                )


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
