from django.apps import AppConfig


class DevicesConfig(AppConfig):
    name = "devices"

    def ready(self) -> None:
        from peering_manager.models.features import register_models

        register_models(*self.get_models())
