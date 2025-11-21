from django.apps import AppConfig
from django.conf import settings
from django.core.cache import cache


class CoreConfig(AppConfig):
    name = "core"

    def ready(self) -> None:
        from core.api import schema  # noqa: F401
        from peering_manager.models.features import register_models

        from . import data_backends  # noqa: F401

        register_models(*self.get_models())

        if settings.DEBUG:
            cache.clear()
