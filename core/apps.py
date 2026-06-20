from django.apps import AppConfig
from django.conf import settings
from django.core.cache import cache


class CoreConfig(AppConfig):
    name = "core"

    def ready(self) -> None:
        from django.db.models.signals import post_delete, post_save

        from core.api import schema  # noqa: F401
        from peering_manager.models.features import register_models

        from . import (
            data_backends,  # noqa: F401
            scheduling,
            system_jobs,  # noqa: F401
        )
        from .models import ScheduledTask

        register_models(*self.get_models())

        # Re-project a scheduled task onto the queue whenever its row changes
        post_save.connect(scheduling.reconcile_scheduled_task, sender=ScheduledTask)
        post_delete.connect(scheduling.reconcile_scheduled_task, sender=ScheduledTask)

        if settings.DEBUG:
            cache.clear()
