import logging

from django_rq.management.commands.rqworker import Command as _Command

from core.scheduling import reconcile_schedules

DEFAULT_QUEUES = ("high", "default", "low")

logger = logging.getLogger("peering.manager.rqworker")


class Command(_Command):
    """
    Subclass django_rq's rqworker to reconcile scheduled tasks at startup, enable the
    built-in scheduler, and default to all configured queues.
    """

    def handle(self, *args, **options):
        reconcile_schedules()

        options["with_scheduler"] = True

        if len(args) < 1:
            queues = ", ".join(DEFAULT_QUEUES)
            logger.warning(
                "No queues have been specified. This process will service the "
                f"following queues by default: {queues}"
            )
            args = DEFAULT_QUEUES

        super().handle(*args, **options)
