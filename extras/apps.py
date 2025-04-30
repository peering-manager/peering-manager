from django.apps import AppConfig


class ExtrasConfig(AppConfig):
    name = "extras"

    def ready(self) -> None:
        from peering_manager.models.features import register_models

        register_models(*self.get_models())
