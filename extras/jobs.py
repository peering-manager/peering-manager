import logging

from django_rq import job

from core.enums import LogLevel

logger = logging.getLogger("peering.manager.extras.jobs")


@job("default")
def render_export_template(export_template, job):
    job.mark_running(
        "Rendering export template.", object=export_template, logger=logger
    )

    rendered = export_template.render()

    if rendered:
        job.set_output(rendered)
    else:
        job.log(
            "No export (or empty) generated.",
            object=export_template,
            level_choice=LogLevel.INFO,
            logger=logger,
        )

    job.mark_completed(
        "Export template rendered.", object=export_template, logger=logger
    )
