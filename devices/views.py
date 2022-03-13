from django.db.models import Count

from devices.filters import ConfigurationFilterSet, PlatformFilterSet
from devices.forms import ConfigurationFilterForm, ConfigurationForm, PlatformForm
from devices.models import Configuration, Platform
from devices.tables import ConfigurationTable, PlatformTable
from peering.models import Router
from peering_manager.views.generics import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)


class ConfigurationList(ObjectListView):
    permission_required = "devices.view_configuration"
    queryset = Configuration.objects.all()
    filterset = ConfigurationFilterSet
    filterset_form = ConfigurationFilterForm
    table = ConfigurationTable
    template_name = "devices/configuration/list.html"


class ConfigurationView(ObjectView):
    permission_required = "devices.view_configuration"
    queryset = Configuration.objects.all()

    def get_extra_context(self, request, instance):
        return {
            "routers": Router.objects.filter(configuration_template=instance),
            "active_tab": "main",
        }


class ConfigurationAdd(ObjectEditView):
    permission_required = "devices.add_configuration"
    queryset = Configuration.objects.all()
    model_form = ConfigurationForm
    template_name = "devices/configuration/add_edit.html"


class ConfigurationEdit(ObjectEditView):
    permission_required = "devices.change_configuration"
    queryset = Configuration.objects.all()
    model_form = ConfigurationForm
    template_name = "devices/configuration/add_edit.html"


class ConfigurationDelete(ObjectDeleteView):
    permission_required = "devices.delete_configuration"
    queryset = Configuration.objects.all()


class ConfigurationBulkDelete(BulkDeleteView):
    permission_required = "devices.delete_configuration"
    queryset = Configuration.objects.all()
    filterset = ConfigurationFilterSet
    table = ConfigurationTable


class PlatformList(ObjectListView):
    permission_required = "devices.view_platform"
    queryset = Platform.objects.annotate(
        router_count=Count("router", distinct=True)
    ).order_by("name")
    table = PlatformTable
    template_name = "devices/platform/list.html"


class PlatformAdd(ObjectEditView):
    permission_required = "devices.add_platform"
    queryset = Platform.objects.all()
    model_form = PlatformForm
    template_name = "devices/platform/add_edit.html"


class PlatformEdit(ObjectEditView):
    permission_required = "devices.change_platform"
    queryset = Platform.objects.all()
    model_form = PlatformForm
    template_name = "devices/platform/add_edit.html"


class PlatformDelete(ObjectDeleteView):
    permission_required = "devices.delete_platform"
    queryset = Platform.objects.all()


class PlatformBulkDelete(BulkDeleteView):
    permission_required = "devices.delete_platform"
    queryset = Platform.objects.all()
    filterset = PlatformFilterSet
    table = PlatformTable
