from django.apps import AppConfig


class PeeringdbConfig(AppConfig):
    name = "peeringdb"
    verbose_name = "PeeringDB"

    def ready(self) -> None:
        from peering_manager.models.features import register_models

        from . import jobs  # noqa: F401

        register_models(*self.get_models())
