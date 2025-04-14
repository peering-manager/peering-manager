from django.apps import AppConfig


class PeeringConfig(AppConfig):
    name = "peering"

    def ready(self) -> None:
        import peering.signals  # noqa: F401
        from peering_manager.models.features import register_models

        register_models(*self.get_models())
