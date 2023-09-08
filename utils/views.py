from django.conf import settings
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as _PermissionRequiredMixin,
)
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from peering_manager.registry import registry

__all__ = ("PermissionRequiredMixin", "GetReturnURLMixin")


class PermissionRequiredMixin(_PermissionRequiredMixin):
    """
    Overrides the original `PermissionRequiredMixin` class to handle the
    `LOGIN_REQUIRED` with `*.view_*` permission.
    """

    def has_permission(self):
        if (
            not settings.LOGIN_REQUIRED
            and isinstance(self.permission_required, str)
            and ".view_" in self.permission_required
        ):
            return True
        else:
            return super().has_permission()


class GetReturnURLMixin:
    """
    Provides logic for determining where a user should be redirected after processing
    a form.
    """

    default_return_url = None

    def get_return_url(self, request, instance=None):
        # Check if `return_url` was specified as a query parameter or form
        # data, use this URL only if it's safe
        return_url = request.GET.get("return_url") or request.POST.get("return_url")
        if return_url and return_url.startswith("/"):
            return return_url

        # Check if the object being modified (if any) has an absolute URL
        if (
            instance is not None
            and instance.pk
            and hasattr(instance, "get_absolute_url")
        ):
            return instance.get_absolute_url()

        # Fall back to the default URL (if specified) for the view
        if self.default_return_url is not None:
            return reverse(self.default_return_url)

        # Try to resolve the list view for the object
        if hasattr(self, "queryset"):
            model_opts = self.queryset.model._meta
            try:
                return reverse(f"{model_opts.app_label}:{model_opts.model_name}_list")
            except NoReverseMatch:
                pass

        # If all fails, send the user to the homepage
        return reverse("home")
