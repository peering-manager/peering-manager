from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django import template
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.module_loading import import_string

from peering_manager.registry import registry
from utils.views import get_viewname

if TYPE_CHECKING:
    from django.db import models
    from django.template import Context

__all__ = ("model_view_tabs",)

register = template.Library()


@register.inclusion_tag("tabs/model_view_tabs.html", takes_context=True)
def model_view_tabs(
    context: Context, instance: models.Model
) -> dict[str, list[dict[str, Any]]]:
    app_label = instance._meta.app_label
    model_name = instance._meta.model_name
    user = context.get("request").user
    tabs: list[dict[str, Any]] = []

    try:
        views = registry["views"][app_label][model_name]
    except KeyError:
        views = []

    for config in views:
        view = (
            import_string(config["view"])
            if type(config["view"]) is str
            else config["view"]
        )
        if tab := getattr(view, "tab", None):
            if tab.permission and not user.has_perm(tab.permission):
                continue

            if attrs := tab.render(instance):
                viewname = get_viewname(instance, action=config["name"])
                active_tab = context.get("tab")
                try:
                    url = reverse(viewname, args=[instance.pk])
                except NoReverseMatch:
                    # No URL has been registered for this view; skip
                    continue
                tabs.append(
                    {
                        "name": config["name"],
                        "url": url,
                        "label": attrs["label"],
                        "badge": attrs["badge"],
                        "weight": attrs["weight"],
                        "is_active": active_tab and active_tab == tab,
                    }
                )

    return {"tabs": sorted(tabs, key=lambda x: x["weight"])}
