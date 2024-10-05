import django_tables2 as tables
from django.utils.safestring import mark_safe
from django_tables2.utils import A

from peering_manager.tables import BaseTable, columns

from ..constants import RQ_TASK_STATUSES

__all__ = (
    "BackgroundQueueTable",
    "BackgroundTaskTable",
    "BackgroundTaskTable",
    "WorkerTable",
)


class RQJobStatusColumn(tables.Column):
    """
    Render a coloured label for the status of an RQ job.
    """

    def render(self, value):
        status = RQ_TASK_STATUSES.get(value)
        return mark_safe(
            f'<span class="badge badge-{status.colour}">{status.label}</span>'
        )

    def value(self, value):
        status = RQ_TASK_STATUSES.get(value)
        return status.label


class BackgroundQueueTable(BaseTable):
    name = tables.Column(verbose_name="Name")
    jobs = tables.Column(
        linkify=("core:background_task_list", [A("index"), "queued"]),
        verbose_name="Queued",
    )
    oldest_job_timestamp = tables.Column(verbose_name="Oldest Task")
    started_jobs = tables.Column(
        linkify=("core:background_task_list", [A("index"), "started"]),
        verbose_name="Active",
    )
    deferred_jobs = tables.Column(
        linkify=("core:background_task_list", [A("index"), "deferred"]),
        verbose_name="Deferred",
    )
    finished_jobs = tables.Column(
        linkify=("core:background_task_list", [A("index"), "finished"]),
        verbose_name="Finished",
    )
    failed_jobs = tables.Column(
        linkify=("core:background_task_list", [A("index"), "failed"]),
        verbose_name="Failed",
    )
    scheduled_jobs = tables.Column(
        linkify=("core:background_task_list", [A("index"), "scheduled"]),
        verbose_name="Scheduled",
    )
    workers = tables.Column(
        linkify=("core:worker_list", [A("index")]), verbose_name="Workers"
    )
    host = tables.Column(accessor="connection_kwargs__host", verbose_name="Host")
    port = tables.Column(accessor="connection_kwargs__port", verbose_name="Port")
    db = tables.Column(accessor="connection_kwargs__db", verbose_name="DB")
    pid = tables.Column(accessor="scheduler__pid", verbose_name="Scheduler PID")

    class Meta(BaseTable.Meta):
        empty_text = "No queues found"
        fields = (
            "name",
            "jobs",
            "oldest_job_timestamp",
            "started_jobs",
            "deferred_jobs",
            "finished_jobs",
            "failed_jobs",
            "scheduled_jobs",
            "workers",
            "host",
            "port",
            "db",
            "pid",
        )
        default_columns = (
            "name",
            "jobs",
            "started_jobs",
            "deferred_jobs",
            "finished_jobs",
            "failed_jobs",
            "scheduled_jobs",
            "workers",
        )


class BackgroundTaskTable(BaseTable):
    id = tables.Column(linkify=("core:background_task", [A("id")]), verbose_name="ID")
    created_at = columns.DateTimeColumn(verbose_name="Created")
    enqueued_at = columns.DateTimeColumn(verbose_name="Enqueued")
    ended_at = columns.DateTimeColumn(verbose_name="Ended")
    status = RQJobStatusColumn(verbose_name="Status", accessor="get_status")
    callable = tables.Column(empty_values=(), verbose_name="Callable")

    class Meta(BaseTable.Meta):
        empty_text = "No tasks found"
        fields = (
            "id",
            "created_at",
            "enqueued_at",
            "ended_at",
            "status",
            "callable",
        )
        default_columns = (
            "id",
            "created_at",
            "enqueued_at",
            "ended_at",
            "status",
            "callable",
        )

    def render_callable(self, value, record):
        try:
            return record.func_name
        except Exception as e:
            return repr(e)


class WorkerTable(BaseTable):
    name = tables.Column(linkify=("core:worker", [A("name")]), verbose_name="Name")
    state = tables.Column(verbose_name="State")
    birth_date = columns.DateTimeColumn(verbose_name="Birth")
    pid = tables.Column(verbose_name="PID")

    class Meta(BaseTable.Meta):
        empty_text = "No workers found"
        fields = ("name", "state", "birth_date", "pid")
        default_columns = ("name", "state", "birth_date", "pid")
