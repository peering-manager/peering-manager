import logging

from django_rq import job

from extras.enums import LogLevel
from net.models import Connection

logger = logging.getLogger("peering.manager.peering.jobs")


@job("default")
def generate_configuration(router, job_result):
    job_result.mark_running(
        "Generating router configuration.", obj=router, logger=logger
    )

    config = router.generate_configuration()

    if config:
        job_result.set_output(config)
    else:
        job_result.log(
            f"No configuration (or empty) generated.",
            obj=router,
            level_choice=LogLevel.INFO,
            logger=logger,
        )

    job_result.mark_completed(
        "Router configuration generated.", obj=router, logger=logger
    )


@job("default")
def import_sessions_to_internet_exchange(internet_exchange, job_result):
    job_result.mark_running(
        "Trying to import peering sessions.", obj=internet_exchange, logger=logger
    )

    connections = Connection.objects.filter(
        internet_exchange_point=internet_exchange, router__isnull=False
    )
    if connections.count() < 1:
        job_result.mark_completed(
            "No usable connections.", obj=internet_exchange, logger=logger
        )
        return False

    job_result.log(
        f"Found {connections.count()} connections.",
        obj=internet_exchange,
        level_choice=LogLevel.INFO,
        logger=logger,
    )

    for connection in connections:
        if not connection.router or not connection.router.is_usable_for_task():
            job_result.log(
                f"Ignored connection {connection}, no router or not usable.",
                obj=internet_exchange,
                level_choice=LogLevel.INFO,
                logger=logger,
            )
            continue

        session_number, asn_number = internet_exchange.import_sessions(connection)
        job_result.log(
            f"Imported {session_number} sessions for {asn_number} autonomous systems.",
            obj=internet_exchange,
            level_choice=LogLevel.INFO,
            logger=logger,
        )

    job_result.mark_completed("Import completed.", obj=internet_exchange, logger=logger)

    return True


@job("default")
def poll_bgp_sessions(router, job_result):
    if not router.is_usable_for_task(job_result=job_result, logger=logger):
        return False

    job_result.mark_running("Polling BGP sessions state.", obj=router, logger=logger)

    success = router.poll_bgp_sessions()

    if success:
        job_result.mark_completed(
            "Successfully polled BGP sessions state.", obj=router, logger=logger
        )
    else:
        job_result.mark_failed(
            "Error while polling BGP sessions state.", obj=router, logger=logger
        )

    return success


@job("default")
def set_napalm_configuration(router, commit, job_result):
    if not router.is_usable_for_task(job_result=job_result, logger=logger):
        return False

    job_result.mark_running(
        "Trying to install configuration.", obj=router, logger=logger
    )

    error, changes = router.set_napalm_configuration(
        router.generate_configuration(), commit=commit
    )

    if error:
        job_result.set_output(error)
        job_result.mark_failed(
            "Failed to install configuration.", obj=router, logger=logger
        )
        return False

    if not changes:
        job_result.mark_completed(
            "No configuration to install.", obj=router, logger=logger
        )
    else:
        job_result.set_output(changes)
        job_result.mark_completed(
            "Configuration installed."
            if commit
            else "Configuration differences found.",
            obj=router,
            logger=logger,
        )

    return True


@job("default")
def test_napalm_connection(router, job_result):
    if not router.is_usable_for_task(job_result=job_result, logger=logger):
        return False

    job_result.mark_running("Trying to connect...", obj=router, logger=logger)

    success = router.test_napalm_connection()

    if success:
        job_result.mark_completed("Connection successful.", obj=router, logger=logger)
    else:
        job_result.mark_failed("Connection failure.", obj=router, logger=logger)

    return success
