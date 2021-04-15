import logging

from django_rq import job

from extras.enums import JobResultStatus
from net.models import Connection

from .enums import DeviceState

logger = logging.getLogger("peering.manager.peering.jobs")


@job("default")
def generate_configuration(router, job_result):
    job_result.mark_running(
        "Generating router configuration.", obj=router, logger=logger
    )
    job_result.save()

    config = router.generate_configuration()

    if config:
        job_result.set_output(config)

    job_result.mark_completed(
        "Router configuration generated.", obj=router, logger=logger
    )
    job_result.save()


@job("default")
def import_peering_sessions_from_router(internet_exchange, job_result):
    job_result.mark_running(
        "Trying to import peering sessions.", obj=internet_exchange, logger=logger
    )
    job_result.save()

    connections = Connection.objects.filter(
        internet_exchange_point=internet_exchange, router__isnull=False
    )
    if connections.count() < 1:
        job_result.mark_completed(
            "No usable connections.", obj=internet_exchange, logger=logger
        )
        job_result.save()
        return False

    job_result.log(
        f"Found {connections.count()} connections.",
        obj=internet_exchange,
        level_choice=LogLevel.INFO,
        logger=logger,
    )
    job_result.save()

    for connection in connections:
        if not connection.router or not connection.router.is_usable_for_task():
            job_result.log(
                f"Ignored connection {connection}, no router or not usable.",
                obj=internet_exchange,
                level_choice=LogLevel.INFO,
                logger=logger,
            )
            job_result.save()
            continue

        session_number, asn_number = internet_exchange.import_sessions(connection)
        job_result.log(
            f"Imported {session_number} sessions for {asn_number} autonomous systems.",
            obj=internet_exchange,
            level_choice=LogLevel.INFO,
            logger=logger,
        )
        job_result.save()

    job_result.mark_completed("Import completed.", obj=internet_exchange, logger=logger)
    job_result.save()

    return True


@job("default")
def poll_peering_sessions(group, job_result):
    job_result.mark_running("Polling peering session states.", obj=group, logger=logger)
    job_result.save()

    success = group.poll_peering_sessions()

    if success:
        job_result.mark_completed(
            "Successfully polled peering session states.", obj=group, logger=logger
        )
    else:
        job_result.mark_failed(
            "Error while polling peering session states.", obj=group, logger=logger
        )
        job_result.save()
        return False

    job_result.save()
    return True


@job("default")
def set_napalm_configuration(router, commit, job_result):
    if not router.is_usable_for_task(job_result=job_result, logger=logger):
        return False

    job_result.mark_running(
        "Trying to install configuration.", obj=router, logger=logger
    )
    job_result.save()

    error, changes = router.set_napalm_configuration(
        router.generate_configuration(), commit=commit
    )

    if error:
        job_result.set_output(error)
        job_result.mark_failed(
            "Failed to install configuration.", obj=router, logger=logger
        )
        job_result.save()
        return False

    job_result.set_output(changes)
    if not changes:
        job_result.mark_completed(
            "No configuration to install.", obj=router, logger=logger
        )
    else:
        job_result.mark_completed(
            "Configuration installed."
            if commit
            else "Configuration differences found.",
            obj=router,
            logger=logger,
        )

    job_result.save()
    return success


@job("default")
def test_napalm_connection(router, job_result):
    if not router.is_usable_for_task(job_result=job_result, logger=logger):
        return False

    job_result.mark_running("Trying to connect...", obj=router, logger=logger)
    job_result.save()

    success = router.test_napalm_connection()

    if success:
        job_result.mark_completed("Connection successful.", obj=router, logger=logger)
    else:
        job_result.mark_failed("Connection failure.", obj=router, logger=logger)

    job_result.save()
    return success
