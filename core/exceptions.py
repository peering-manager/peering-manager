import logging
import traceback

__all__ = ("FetchError", "PushError", "SynchronisationError", "exception_handler")


def exception_handler(rq_job, exc_type, exc_value, trace):
    """
    Sets result's details according to the exception that occurred while running the job.
    """
    from .models import Job

    logger = logging.getLogger("peering.manager.core.jobs")

    try:
        job = Job.objects.get(job_id=rq_job.id)
    except Job.DoesNotExist:
        logger.error(f"could not find job id {rq_job.id}, cannot log exception")

    job.set_output("".join(traceback.format_exception(exc_type, exc_value, trace)))
    job.mark_errored(
        "An exception occurred, see output for more details.", logger=logger
    )


class FetchError(Exception):
    pass


class PushError(Exception):
    pass


class SynchronisationError(Exception):
    pass
