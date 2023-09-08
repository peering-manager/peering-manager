import django_tables2 as tables
from django.conf import settings

from peering_manager.tables import BaseTable, columns

from ..models import Job


class JobTable(BaseTable):
    pk = columns.SelectColumn()
    object_type = columns.ContentTypeColumn(verbose_name="Object type")
    object = tables.Column(linkify=True)
    created = tables.DateTimeColumn(linkify=True, format=settings.SHORT_DATETIME_FORMAT)
    started = tables.DateTimeColumn(linkify=True, format=settings.SHORT_DATETIME_FORMAT)
    completed = tables.DateTimeColumn(
        linkify=True, format=settings.SHORT_DATETIME_FORMAT
    )
    status = columns.ChoiceFieldColumn()
    data = tables.TemplateColumn(
        """
        <span class="badge badge-success">{{ value.total.success }}</span>
        <span class="badge badge-info">{{ value.total.info }}</span>
        <span class="badge badge-warning">{{ value.total.warning }}</span>
        <span class="badge badge-danger">{{ value.total.failure }}</span>
        """,
        verbose_name="Results",
        orderable=False,
        attrs={"td": {"class": "text-nowrap"}},
    )

    class Meta(BaseTable.Meta):
        model = Job
        fields = (
            "pk",
            "object_type",
            "object",
            "name",
            "status",
            "created",
            "started",
            "completed",
            "user",
            "job_id",
        )
        default_columns = (
            "pk",
            "object_type",
            "object",
            "name",
            "status",
            "created",
            "started",
            "completed",
            "user",
        )
