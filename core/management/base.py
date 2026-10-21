from django.core.management.base import BaseCommand

from core.context_managers import system_change_logging

__all__ = ("SystemCommand",)


class SystemCommand(BaseCommand):
    """
    Base class of a command that cron can run with changes logged under the system user.
    """

    def execute(self, *args, **options):
        with system_change_logging():
            return super().execute(*args, **options)
