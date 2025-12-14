"""
Custom permission classes for the Peering Manager REST API.
"""

import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import permissions

from users.models import Token
from users.models import TokenObjectPermission as TokenObjectPermissionModel

logger = logging.getLogger(__name__)


class TokenObjectPermissionMixin(permissions.BasePermission):
    """
    Permission class that checks if an API token has permission for a specific object.

    By default, tokens are allowed to perform all actions unless explicitly restricted.
    Token permissions apply to all users, including superusers.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return bool(request.user) and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if the token has permission for this specific object.
        """
        # If not using token auth, allow (Django permissions handle this)
        if not isinstance(request.auth, Token):
            return True

        token = request.auth
        action = getattr(view, "action", None)
        content_type = ContentType.objects.get_for_model(obj)

        # Check if there's an explicit permission for this token/object pair
        try:
            token_permission = TokenObjectPermissionModel.objects.get(
                token=token, content_type=content_type, object_id=obj.pk
            )
            has_perm = token_permission.has_permission(action)
            logger.info(
                f"TokenObjectPermission: Token {token.key[:8]}... action '{action}' on {content_type.model} #{obj.pk}: {has_perm}"
            )
            return has_perm
        except TokenObjectPermissionModel.DoesNotExist:
            # No explicit permission set - use configured default mode
            default_mode = getattr(settings, "TOKEN_PERMISSIONS_DEFAULT_MODE", "allow")

            # Check if this object enforces specific behavior
            if (
                hasattr(obj, "enforce_token_permissions")
                and obj.enforce_token_permissions
            ):
                logger.info(
                    f"TokenObjectPermission: Object {content_type.model} #{obj.pk} requires explicit permissions, denying"
                )
                return False

            # Use global default mode
            allow = default_mode == "allow"
            logger.debug(
                f"TokenObjectPermission: No permission found, default mode '{default_mode}', {'allowing' if allow else 'denying'}"
            )
            return allow


class TokenObjectPermission(TokenObjectPermissionMixin):
    """
    Standalone permission class for token object permissions.

    Use this directly in ViewSets that want to enforce token object permissions.
    """
