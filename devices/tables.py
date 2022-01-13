import django_tables2 as tables

from devices.models import Configuration, Platform
from utils.tables import (
    BaseTable,
    BooleanColumn,
    ButtonsColumn,
    SelectColumn,
    TagColumn,
)


class ConfigurationTable(BaseTable):
    pk = SelectColumn()
    name = tables.Column(linkify=True)
    jinja2_trim = BooleanColumn(verbose_name="Trim")
    jinja2_lstrip = BooleanColumn(verbose_name="Lstrip")
    tags = TagColumn(url_name="devices:configuration_list")
    actions = ButtonsColumn(Configuration)

    class Meta(BaseTable.Meta):
        model = Configuration
        fields = (
            "pk",
            "name",
            "jinja2_trim",
            "jinja2_lstrip",
            "updated",
            "tags",
            "actions",
        )
        default_columns = ("pk", "name", "updated", "actions")


class PlatformTable(BaseTable):
    pk = SelectColumn()
    router_count = tables.Column(
        verbose_name="Routers",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    actions = ButtonsColumn(Platform, buttons=("edit", "delete"))

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
            "actions",
        )
        default_columns = (
            "pk",
            "name",
            "router_count",
            "napalm_driver",
            "password_algorithm",
            "description",
            "actions",
        )
