import django_tables2 as tables

from peering_manager.tables import BaseTable, columns

from ..models import ScheduledTask

__all__ = ("ScheduledTaskTable",)


class ScheduledTaskTable(BaseTable):
    task = tables.Column(accessor="task_label", linkify=True, orderable=False, verbose_name="Task")
    enabled = columns.BooleanColumn()
    interval = tables.Column(verbose_name="Interval (minutes)")
    last_run = columns.DateTimeColumn(accessor="last_job.completed", orderable=False, verbose_name="Last run")
    next_run = columns.DateTimeColumn(accessor="next_run", orderable=False)
    actions = columns.ActionsColumn(actions=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = ScheduledTask
        fields = ("task", "enabled", "interval", "last_run", "next_run")
        default_columns = ("task", "enabled", "interval", "last_run", "next_run")
