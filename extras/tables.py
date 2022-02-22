import django_tables2 as tables
from django.conf import settings

from utils.tables import BaseTable, ButtonsColumn, SelectColumn

from .models import IXAPI, JobResult, RipeIrr


class IXAPITable(BaseTable):
    name = tables.Column(linkify=True)
    url = tables.URLColumn()
    actions = ButtonsColumn(IXAPI)

    class Meta(BaseTable.Meta):
        model = IXAPI
        fields = ("name", "url", "api_key", "actions")
        default_columns = ("name", "url", "api_key", "actions")


class JobResultTable(BaseTable):
    pk = SelectColumn()
    obj_type = tables.Column(verbose_name="Object Type", accessor="obj_type__name")
    created = tables.DateTimeColumn(linkify=True, format=settings.SHORT_DATETIME_FORMAT)
    status = tables.TemplateColumn(
        """
        {% if record.status == 'failed' %}
        <span class="badge badge-danger">Failed</span>
        {% elif record.status == 'errored' %}
        <span class="badge badge-danger">Errored</span>
        {% elif record.status == 'pending' %}
        <span class="badge badge-primary">Pending</span>
        {% elif record.status == 'running' %}
        <span class="badge badge-warning">Running</span>
        {% elif record.status == 'completed' %}
        <span class="badge badge-success">Completed</span>
        {% else %}
        <span class="badge badge-secondary">Unknown</span>
        {% endif %}
        """
    )
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
        model = JobResult
        fields = (
            "pk",
            "created",
            "obj_type",
            "name",
            "duration",
            "completed",
            "user",
            "status",
            "data",
        )
        default_columns = ("pk", "created", "name", "user", "status", "data")


class RipeIrrTable(BaseTable):
    name = tables.Column(linkify=True)

    class Meta(BaseTable.Meta):
        model = RipeIrr
        fields = ("name",)
        default_columns = ("name",)
