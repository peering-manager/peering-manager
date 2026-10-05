import logging
import traceback

__all__ = (
    "FetchError",
    "JobFailedError",
    "PushError",
    "SynchronisationError",
    "exception_handler",
)


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
        return

    # RQ gives a stack summary instead of a traceback for a job it found abandoned
    if isinstance(trace, traceback.StackSummary):
        output = [*trace.format(), *traceback.format_exception_only(exc_type, exc_value)]
    else:
        output = traceback.format_exception(exc_type, exc_value, trace)
    job.set_output("".join(output))
    job.mark_errored("An exception occurred, see output for more details.", logger=logger)


class FetchError(Exception):
    pass


class JobFailedError(Exception):
    """
    Raised to signal that the job failed for a known/handled reason. This should be
    caught to mark the job as `FAILED` (rather than `ERRORED`, which is for unhandled
    exceptions).
    """


class PushError(Exception):
    pass


class SynchronisationError(Exception):
    pass
