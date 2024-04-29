import logging

from django.template.defaultfilters import pluralize
from django_rq import job

from core.enums import DataSourceStatus, LogLevel
from core.exceptions import SynchronisationError
from net.models import Connection

logger = logging.getLogger("peering.manager.peering.jobs")


@job("default")
def render_configuration(router, job):
    job.mark_running("Rendering router configuration.", object=router, logger=logger)

    config = router.render_configuration()

    if config:
        job.set_output(config)
    else:
        job.log(
            "No configuration (or empty) generated.",
            object=router,
            level_choice=LogLevel.INFO,
            logger=logger,
        )

    job.mark_completed("Router configuration rendered.", object=router, logger=logger)


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


@job("default")
def poll_bgp_sessions(router, job):
    if not router.is_usable_for_task(job=job, logger=logger):
        job.mark_completed("Task cancelled")
        return False

    job.mark_running("Polling BGP sessions state.", object=router, logger=logger)

    success, count = router.poll_bgp_sessions()

    if success:
        job.mark_completed(
            f"Successfully polled BGP {count} session{pluralize(count)} state.",
            object=router,
            logger=logger,
        )
    else:
        job.mark_failed(
            "Error while polling BGP sessions state.", object=router, logger=logger
        )

    return success


@job("default")
def set_napalm_configuration(router, commit, job):
    if not router.is_usable_for_task(job=job, logger=logger):
        job.mark_completed("Task cancelled")
        return False

    job.mark_running("Trying to install configuration.", object=router, logger=logger)

    error, changes = router.set_napalm_configuration(
        router.render_configuration(), commit=commit
    )

    if error:
        job.set_output(error)
        job.mark_failed(
            "Failed to install configuration.", object=router, logger=logger
        )
        return False

    if not changes:
        job.mark_completed("No configuration to install.", object=router, logger=logger)
    else:
        job.set_output(changes)
        job.mark_completed(
            (
                "Configuration installed."
                if commit
                else "Configuration differences found."
            ),
            object=router,
            logger=logger,
        )

    return True


@job("default")
def test_napalm_connection(router, job):
    if not router.is_usable_for_task(job=job, logger=logger):
        job.mark_completed("Task cancelled")
        return False

    job.mark_running("Trying to connect...", object=router, logger=logger)

    success = router.test_napalm_connection()

    if success:
        job.mark_completed("Connection successful.", object=router, logger=logger)
    else:
        job.mark_failed("Connection failure.", object=router, logger=logger)

    return success


@job("default")
def push_configuration_to_data_source(router, job):
    if not router.data_source or not router.data_path:
        job.mark_completed("No data source and file to push configuration to")
        return False

    job.mark_running(
        f"Pushing router configuration to {router.data_source}:{router.data_path}.",
        object=router,
        logger=logger,
    )

    try:
        router.push(save=True)
        job.mark_completed("Router configuration pushed.", object=router, logger=logger)
    except Exception as e:
        job.set_output(str(e))
        job.mark_failed("Failed to push to data source.", object=router, logger=logger)
        router.data_source.status = DataSourceStatus.FAILED
        router.data_source.save()

        if isinstance(e, SynchronisationError):
            logger.error(e)
            return False

        raise e

    return True
