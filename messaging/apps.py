from django.apps import AppConfig


class MessagingConfig(AppConfig):
    name = "messaging"

    def ready(self) -> None:
        from peering_manager.models.features import register_models

        register_models(*self.get_models())
