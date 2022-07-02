import logging

from django_rq import job

from extras.enums import LogLevel

from .sync import PeeringDB

logger = logging.getLogger("peering.manager.peeringdb.jobs")


# One hour and 30 minutes timeout as this process can take long depending on the host
# properties
@job("default", timeout=5400)
def synchronize(job_result):
    job_result.mark_running("Synchronizing PeeringDB local data.", logger=logger)

    api = PeeringDB()
    last_sync = api.get_last_sync_time()
    synchronization = api.update_local_database(last_sync)

    if not synchronization:
        job_result.mark_completed("Nothing to synchronize.", logger=logger)
        return

    job_result.log(
        f"Created {synchronization.created} objects",
        level_choice=LogLevel.INFO,
        logger=logger,
    )
    job_result.log(
        f"Updated {synchronization.updated} objects",
        level_choice=LogLevel.INFO,
        logger=logger,
    )
    job_result.log(
        f"Deleted {synchronization.deleted} objects",
        level_choice=LogLevel.INFO,
        logger=logger,
    )

    job_result.mark_completed("Synchronization finished.", logger=logger)
