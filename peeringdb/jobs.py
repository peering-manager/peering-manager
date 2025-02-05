import logging

from django_rq import job

from core.enums import LogLevel
from peering.models import AutonomousSystem

from .sync import PeeringDB

logger = logging.getLogger("peering.manager.peeringdb.jobs")


# One hour and 30 minutes timeout as this process can take long depending on the host
# properties
@job("default", timeout=5400)
def synchronise(job):
    job.mark_running("Synchronising PeeringDB local data.", logger=logger)

    synchronisation = PeeringDB().update_local_database()

    if not synchronisation:
        job.mark_completed("Nothing to synchronise.", logger=logger)
        return

    job.log(
        f"Created {synchronisation.created} objects",
        level_choice=LogLevel.INFO,
        logger=logger,
    )
    job.log(
        f"Updated {synchronisation.updated} objects",
        level_choice=LogLevel.INFO,
        logger=logger,
    )
    job.log(
        f"Deleted {synchronisation.deleted} objects",
        level_choice=LogLevel.INFO,
        logger=logger,
    )

    updated_as_count = 0
    for autonomous_system in AutonomousSystem.objects.defer("prefixes"):
        if autonomous_system.synchronise_with_peeringdb():
            updated_as_count += 1

    job.log(
        f"Updating values for {updated_as_count} autonomous systems",
        level_choice=LogLevel.INFO,
        logger=logger,
    )

    job.mark_completed("Synchronisation finished.", logger=logger)
