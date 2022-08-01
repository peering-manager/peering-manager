import logging

from django_rq import job

from extras.enums import LogLevel

logger = logging.getLogger("peering.manager.extras.jobs")


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
