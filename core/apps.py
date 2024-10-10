from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from core.api import schema  # noqa: F401

        from . import data_backends  # noqa: F401
