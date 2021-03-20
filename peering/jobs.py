import logging

from django_rq import job

from extras.enums import JobResultStatus

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

    log = 'Ignoring peering sessions, reason: "{}"'
    if not internet_exchange.router:
        log = log.format(internet_exchange.name.lower(), "no router attached.")
    elif not internet_exchange.router.platform:
        log = log.format(
            internet_exchange.name.lower(), "router with unsupported platform."
        )
    else:
        log = None

    # No point of discovering from router if platform is none or is not supported
    if log:
        job_result.mark_completed(log, obj=internet_exchange, logger=logger)
        job_result.save()
        return False

    # Build a list based on prefixes based on PeeringDB records
    prefixes = [p.prefix for p in internet_exchange.get_prefixes()]
    # No prefixes found
    if not prefixes:
        job_result.mark_failed(
            "No prefixes found.", obj=internet_exchange, logger=logger
        )
        job_result.save()
        return False

    log = "Found {} prefixes ({})".format(
        len(prefixes), ", ".join([str(prefix) for prefix in prefixes])
    )
    job_result.log(
        log, obj=internet_exchange, level_choice=LogLevel.INFO, logger=logger
    )
    job_result.save()

    sessions = internet_exchange.router.get_bgp_neighbors()
    (
        as_number,
        session_number,
        ignored_as_number,
    ) = internet_exchange.import_peering_sessions(bgp_sessions, prefixes)

    job_result.log(
        "Ignored {ignored_as_number} autonomous systems.",
        obj=internet_exchange,
        level_choice=LogLevel.INFO,
        logger=logger,
    )
    job_result.mark_completed(
        "Imported {session_number} sessions for {as_number} autonomous systems.",
        obj=internet_exchange,
        logger=logger,
    )
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
