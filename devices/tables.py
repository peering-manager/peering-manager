import django_tables2 as tables
from django.utils.safestring import mark_safe

from utils.tables import BaseTable, ButtonsColumn, SelectColumn

from .models import Platform


class PlatformTable(BaseTable):
    pk = SelectColumn()
    router_count = tables.Column(
        verbose_name="Routers",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    buttons = ButtonsColumn(Platform, pk_field="slug")

    class Meta(BaseTable.Meta):
        model = Platform
        fields = (
            "pk",
            "name",
            "router_count",
            "slug",
            "napalm_driver",
            "napalm_args",
            "password_algorithm",
            "description",
            "buttons",
        )
        default_columns = (
            "pk",
            "name",
            "router_count",
            "napalm_driver",
            "password_algorithm",
            "description",
            "buttons",
        )
