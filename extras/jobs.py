import logging
import traceback

from django_rq import job

from extras.enums import LogLevel
from extras.models import JobResult

logger = logging.getLogger("peering.manager.extras.jobs")


def exception_handler(rq_job, exc_type, exc_value, trace):
    """
    Sets result's details according to the exception that occurred while running the job.
    """
    try:
        job = JobResult.objects.get(job_id=rq_job.id)
    except JobResult.DoesNotExist:
        logger.error(f"could not find job id {rq_job.id}, cannot log exception")

    job.set_output("".join(traceback.format_exception(exc_type, exc_value, trace)))
    job.mark_errored(
        "An exception occurred, see output for more details.", logger=logger
    )


@job("default")
def render_export_template(export_template, job_result):
    job_result.mark_running(
        "Rendering export template.", obj=export_template, logger=logger
    )

    rendered = export_template.render()

    if rendered:
        job_result.set_output(rendered)
    else:
        job_result.log(
            f"No export (or empty) generated.",
            obj=export_template,
            level_choice=LogLevel.INFO,
            logger=logger,
        )

    job_result.mark_completed(
        "Export template rendered.", obj=export_template, logger=logger
    )
