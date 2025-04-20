from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as _PermissionRequiredMixin,
)
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from peering_manager.registry import VIEWS_KEY, registry

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db import models

__all__ = (
    "GetReturnURLMixin",
    "PermissionRequiredMixin",
    "ViewTab",
    "get_viewname",
    "register_model_view",
)


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
        return super().has_permission()


class GetReturnURLMixin:
    """
    Provides logic for determining where a user should be redirected after processing
    a form.
    """

    default_return_url = None

    @staticmethod
    def is_relative_url(url):
        is_absolute = bool(urlparse(url).netloc)
        count_leading_slash = len(url) - len(url.lstrip("/"))
        return url and not is_absolute and count_leading_slash <= 1

    def get_return_url(self, request, instance=None):
        # Check if `return_url` was specified as a query parameter or form
        # data, use this URL only if it's not absolute
        return_url = request.GET.get("return_url") or request.POST.get("return_url")
        if return_url and self.is_relative_url(return_url):
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


class ViewTab:
    """
    ViewTabs are used for navigation among multiple object-specific views, such as the
    changelog or journal for a particular object.
    """

    def __init__(
        self,
        label: str,
        badge: str | None = None,
        weight: int = 1000,
        permission: str | None = None,
        hide_if_empty: bool = False,
    ) -> None:
        self.label = label
        self.badge = badge
        self.weight = weight
        self.permission = permission
        self.hide_if_empty = hide_if_empty

    def render(self, instance: models.Model) -> dict[str, Any] | None:
        """Return the attributes needed to render a tab in HTML."""
        badge_value = self._get_badge_value(instance)
        if self.badge and self.hide_if_empty and not badge_value:
            return None
        return {"label": self.label, "badge": badge_value, "weight": self.weight}

    def _get_badge_value(self, instance: models.Model) -> str | None:
        if not self.badge:
            return None
        if callable(self.badge):
            return self.badge(instance)
        return self.badge


def get_viewname(
    model: type[models.Model], action: str | None = None, rest_api: bool = False
) -> str:
    """
    Return the view name for a given model and action.
    """
    app_label = model._meta.app_label
    model_name = model._meta.model_name

    if rest_api:
        viewname = f"{app_label}-api:{model_name}"
        if action:
            viewname += f"-{action}"
    else:
        viewname = f"{app_label}:{model_name}"
        if action:
            viewname += f"_{action}"

    return viewname


def register_model_view(
    model: type[models.Model],
    name: str = "",
    path: str | None = None,
    detail: bool = True,
    kwargs: Any | None = None,
) -> Callable[..., Any]:
    """
    A decorator to reguster a view for any model. This is mostly used to inject tabs
    within a model detail view. This can be used like:

        @register_model_view(AutonomousSystem, "myview", path="my-own-view")
        class MyView(ObjectView):
            ...

    This will automatically create a URL path for the view like
    `/peering/autonomoussystem/<pk>/my-own-view/` resolvable by the name
    `peering:autonomoussystem_myview`.
    """

    def _wrapper(cls):
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        if model_name not in registry[VIEWS_KEY][app_label]:
            registry[VIEWS_KEY][app_label][model_name] = []

        registry[VIEWS_KEY][app_label][model_name].append(
            {
                "name": name,
                "view": cls,
                "path": path if path is not None else name,
                "detail": detail,
                "kwargs": kwargs or {},
            }
        )

        return cls

    return _wrapper
