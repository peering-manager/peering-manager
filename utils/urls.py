from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import path
from django.utils.module_loading import import_string
from django.views.generic import View

from peering_manager.registry import VIEWS_KEY, registry

if TYPE_CHECKING:
    from django.urls import URLPattern

__all__ = ("get_model_urls",)


def get_model_urls(
    app_label: str, model_name: str, detail: bool = True
) -> list[URLPattern]:
    """
    Return a list of URL paths for views registered to the given model.
    """
    paths: list[URLPattern] = []

    try:
        views = [
            v
            for v in registry[VIEWS_KEY][app_label][model_name]
            if v["detail"] == detail
        ]
    except KeyError:
        return []

    for config in views:
        if type(config["view"]) is str:
            view = import_string(config["view"])
        else:
            view = config["view"]

        if issubclass(view, View):
            view = view.as_view()

        name = f"{model_name}_{config['name']}" if config["name"] else model_name
        url_path = f"{config['path']}/" if config["path"] else ""
        paths.append(
            path(route=url_path, view=view, name=name, kwargs=config["kwargs"])
        )

    return paths
