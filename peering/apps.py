from django.apps import AppConfig


class PeeringConfig(AppConfig):
    name = "peering"

    def ready(self):
        import peering.signals  # noqa: F401
