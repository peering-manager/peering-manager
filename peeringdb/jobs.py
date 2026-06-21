from __future__ import annotations

from core.enums import JobInterval
from peering.models import AutonomousSystem
from peering_manager.jobs import JobRunner, system_job

from .sync import PeeringDB

# 1 hour and 30 minutes timeout as this process can take long depending on the host
# properties and PeeringDB API responsiveness
PEERINGDB_SYNC_TIMEOUT = 5400


@system_job(
    interval=JobInterval.DAILY,
    key="peeringdb-synchronisation",
    label="PeeringDB synchronisation",
    min_interval=JobInterval.HOURLY,
)
class PeeringDBSynchronisationJob(JobRunner):
    """
    Refresh the local PeeringDB cache and update each registered AS with values
    sourced from PeeringDB.
    """

    job_timeout = PEERINGDB_SYNC_TIMEOUT

    class Meta:
        name = "PeeringDB synchronisation"

    def run(self, *args, **kwargs) -> None:
        synchronisation = PeeringDB().update_local_database()

        if not synchronisation:
            self.logger.info("Nothing to synchronise.")
            return

        self.logger.info(f"Created {synchronisation.created} objects")
        self.logger.info(f"Updated {synchronisation.updated} objects")
        self.logger.info(f"Deleted {synchronisation.deleted} objects")

        updated_as_count = 0
        for autonomous_system in AutonomousSystem.objects.all():
            if autonomous_system.synchronise_with_peeringdb():
                updated_as_count += 1

        self.logger.info(f"Updating values for {updated_as_count} autonomous systems")
