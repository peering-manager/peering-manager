import ipaddress
from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone
from rest_framework import authentication, exceptions
from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
    DjangoModelPermissions,
)

from users.models import Token


def get_client_ip(request) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    http_headers = ["HTTP_X_REAL_IP", "HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"]

    for header in http_headers:
        if header not in request.META:
            continue

        ip = request.META[header].split(",")[0].strip()
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            ip = urlparse(f"//{ip}").hostname

        try:
            return ipaddress.ip_address(ip)
        except ValueError as exc:
            raise ValueError(f"Invalid IP address set for {header}: {ip}") from exc

    return None


class TokenAuthentication(authentication.TokenAuthentication):
    """
    An authentication method which honors Token expiration times.
    """

    model = Token

    def authenticate(self, request):
        result = super().authenticate(request)

        if result:
            token = result[1]

            if token.allowed_ips:
                client_ip = get_client_ip(request)
                if client_ip is None:
                    raise exceptions.AuthenticationFailed(
                        "Client IP address could not be determined for validation. "
                        "Check that the HTTP server is correctly configured to pass "
                        "the required header(s)."
                    )
                if not token.validate_client_ip(client_ip):
                    raise exceptions.AuthenticationFailed(
                        f"Source IP {client_ip} is not permitted to authenticate "
                        "using this token."
                    )

        return result

    def authenticate_credentials(self, key):
        model = self.get_model()

        try:
            token = model.objects.prefetch_related("user").get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token") from None

        # Enforce the Token's expiration time
        if token.is_expired:
            raise exceptions.AuthenticationFailed("Token expired")

        # 60 seconds delay to avoid updating last_used too frequently
        if (
            not token.last_used
            or (timezone.now() - token.last_used).total_seconds() > 60
        ):
            Token.objects.filter(pk=token.pk).update(last_used=timezone.now())

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
