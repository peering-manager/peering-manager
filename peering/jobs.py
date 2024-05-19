import logging

from django_rq import job

from core.enums import LogLevel
from net.models import Connection

logger = logging.getLogger("peering.manager.peering.jobs")


@job("default")
def import_sessions_to_internet_exchange(internet_exchange, job):
    job.mark_running(
        "Trying to import peering sessions.", object=internet_exchange, logger=logger
    )

    connections = Connection.objects.filter(
        internet_exchange_point=internet_exchange, router__isnull=False
    )
    if connections.count() < 1:
        job.mark_completed(
            "No usable connections.", object=internet_exchange, logger=logger
        )
        return False

    job.log(
        f"Found {connections.count()} connections.",
        object=internet_exchange,
        level_choice=LogLevel.INFO,
        logger=logger,
    )

    for connection in connections:
        if not connection.router or not connection.router.is_usable_for_task():
            job.log(
                f"Ignored connection {connection}, no router or not usable.",
                object=internet_exchange,
                level_choice=LogLevel.INFO,
                logger=logger,
            )
            continue

        session_number, asn_number = internet_exchange.import_sessions(connection)
        job.log(
            f"Imported {session_number} sessions for {asn_number} autonomous systems.",
            object=internet_exchange,
            level_choice=LogLevel.INFO,
            logger=logger,
        )

    job.mark_completed("Import completed.", object=internet_exchange, logger=logger)

    return True
