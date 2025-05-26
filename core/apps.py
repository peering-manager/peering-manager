from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self) -> None:
        from core.api import schema  # noqa: F401
        from peering_manager.models.features import register_models

        from . import data_backends  # noqa: F401

        register_models(*self.get_models())
