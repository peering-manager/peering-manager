from django.apps import AppConfig


class BgpConfig(AppConfig):
    name = "bgp"
    verbose_name = "BGP"

    def ready(self) -> None:
        from peering_manager.models.features import register_models

        register_models(*self.get_models())
