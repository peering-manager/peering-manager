import logging
import sys

from django.core.management.base import BaseCommand

from core.system_jobs import HousekeepingJob

VERBOSITY_TO_LOG_LEVEL = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
    3: logging.DEBUG,
}


class Command(BaseCommand):
    help = (
        "Perform housekeeping tasks. This is also scheduled to run periodically "
        "by the rqworker; the command remains available for ad-hoc invocation."
    )

    def handle(self, *args, **options):
        log_level = VERBOSITY_TO_LOG_LEVEL.get(options["verbosity"], logging.INFO)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        runner_logger = logging.getLogger("peering.manager.jobs.housekeeping")
        runner_logger.addHandler(handler)
        runner_logger.setLevel(log_level)
        runner_logger.propagate = False

        try:
            HousekeepingJob(job=None).run()
        finally:
            runner_logger.removeHandler(handler)

        self.stdout.write(self.style.SUCCESS("Finished."))
