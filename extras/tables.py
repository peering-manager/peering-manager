from tabnanny import verbose

import django_tables2 as tables
from django.conf import settings

from utils.tables import (
    BaseTable,
    BooleanColumn,
    ButtonsColumn,
    ContentTypeColumn,
    SelectColumn,
)

from .models import IXAPI, ConfigContext, ConfigContextAssignment, JobResult


class ConfigContextTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    is_active = BooleanColumn(verbose_name="Active")
    actions = ButtonsColumn(ConfigContext)

    class Meta(BaseTable.Meta):
        model = ConfigContext
        fields = ("pk", "name", "description", "is_active")
        default_columns = ("name", "description", "is_active")


class ConfigContextAssignmentTable(BaseTable):
    content_type = ContentTypeColumn(verbose_name="Object Type")
    object = tables.Column(linkify=True, orderable=False)
    config_context = tables.Column(linkify=True)
    actions = ButtonsColumn(model=ConfigContextAssignment, buttons=("edit", "delete"))

    class Meta(BaseTable.Meta):
        model = ConfigContextAssignment
        fields = ("content_type", "object", "config_context", "weight", "actions")
        default_columns = (
            "content_type",
            "object",
            "config_context",
            "weight",
            "actions",
        )


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
    obj_type = ContentTypeColumn(verbose_name="Object type")
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
        default_columns = ("created", "name", "user", "status", "data")
