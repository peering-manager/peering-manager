import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns

from .models import Configuration, Platform

__all__ = ("ConfigurationTable", "PlatformTable")


class ConfigurationTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    jinja2_trim = columns.BooleanColumn(verbose_name="Trim")
    jinja2_lstrip = columns.BooleanColumn(verbose_name="Lstrip")
    tags = columns.TagColumn(url_name="devices:configuration_list")

    class Meta(PeeringManagerTable.Meta):
        model = Configuration
        fields = (
            "pk",
            "id",
            "name",
            "jinja2_trim",
            "jinja2_lstrip",
            "updated",
            "tags",
            "actions",
        )
        default_columns = ("pk", "name", "updated", "actions")


class PlatformTable(PeeringManagerTable):
    router_count = tables.Column(
        verbose_name="Routers",
        attrs={"td": {"class": "text-center"}, "th": {"class": "text-center"}},
    )
    actions = columns.ActionsColumn(actions=("edit", "delete"))

    class Meta(PeeringManagerTable.Meta):
        model = Platform
        fields = (
            "pk",
            "id",
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
