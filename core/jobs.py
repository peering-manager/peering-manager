import logging

from django_rq import job

from .enums import *
from .exceptions import SynchronisationError

logger = logging.getLogger("peering.manager.core.jobs")


@job("default")
def synchronise_datasource(object, job):
    job.mark_running(
        "Starting data source synchronisation", object=object, logger=logger
    )

    try:
        object.synchronise()
    except Exception as e:
        job.set_output(str(e))
        job.mark_failed(
            "Failed to synchronise data source.", object=object, logger=logger
        )
        object.status = DataSourceStatus.FAILED
        object.save()

        if isinstance(e, SynchronisationError):
            logger.error(e)
            return

        raise e

    job.mark_completed(
        "Successfully synchronised data source.", object=object, logger=logger
    )
