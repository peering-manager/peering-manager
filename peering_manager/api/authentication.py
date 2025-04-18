from django.conf import settings
from rest_framework import authentication, exceptions
from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
    DjangoModelPermissions,
)

from users.models import Token


class TokenAuthentication(authentication.TokenAuthentication):
    """
    An authentication method which honors Token expiration times.
    """

    model = Token

    def authenticate_credentials(self, key):
        model = self.get_model()

        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token") from None

        # Enforce the Token's expiration time
        if token.is_expired:
            raise exceptions.AuthenticationFailed("Token expired")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive")

        return token.user, token


class TokenPermissions(DjangoModelPermissions):
    """
    Permissions handler extending DjangoModelPermissions to validate Tokens write
    ability for unsafe requests (POST/PUT/PATCH/DELETE).
    """

    def __init__(self):
        # If LOGIN_REQUIRED, don't allow non-authenticated users
        self.authenticated_users_only = settings.LOGIN_REQUIRED
        super().__init__()

    def has_permission(self, request, view):
        # If token authentication is in use, verify that the token allows write
        # operations (for unsafe methods).
        if (
            request.method not in SAFE_METHODS
            and isinstance(request.auth, Token)
            and not request.auth.write_enabled
        ):
            return False
        # If action is not part of default CRUD, allow it
        # Restriction must be performed in the view itself
        if hasattr(view, "action") and view.action not in [
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            return True
        return super().has_permission(request, view)


class IsAuthenticatedOrLoginNotRequired(BasePermission):
    """
    Returns `True` if the user is authenticated or `LOGIN_REQUIRED` is `False`.
    """

    def has_permission(self, request, view):
        return not settings.LOGIN_REQUIRED or request.user.is_authenticated
