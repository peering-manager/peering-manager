from django.db.models import Count
from django.shortcuts import get_object_or_404

from devices.filters import ConfigurationFilterSet, PlatformFilterSet
from devices.forms import ConfigurationFilterForm, ConfigurationForm, PlatformForm
from devices.models import Configuration, Platform
from devices.tables import ConfigurationTable, PlatformTable
from peering.models import Router
from utils.views import (
    AddOrEditView,
    BulkDeleteView,
    DeleteView,
    DetailsView,
    ModelListView,
    PermissionRequiredMixin,
)


class ConfigurationList(PermissionRequiredMixin, ModelListView):
    permission_required = "devices.view_configuration"
    queryset = Configuration.objects.all()
    filter = ConfigurationFilterSet
    filter_form = ConfigurationFilterForm
    table = ConfigurationTable
    template = "devices/configuration/list.html"


class ConfigurationAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "devices.add_configuration"
    model = Configuration
    form = ConfigurationForm
    template = "devices/configuration/add_edit.html"
    return_url = "devices:configuration_list"


class ConfigurationDetails(DetailsView):
    permission_required = "devices.view_configuration"
    queryset = Configuration.objects.all()

    def get_context(self, request, **kwargs):
        instance = get_object_or_404(self.queryset, **kwargs)
        return {
            "instance": instance,
            "routers": Router.objects.filter(configuration_template=instance),
            "active_tab": "main",
        }


class ConfigurationEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "devices.change_configuration"
    model = Configuration
    form = ConfigurationForm
    template = "devices/configuration/add_edit.html"


class ConfigurationDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "devices.delete_configuration"
    model = Configuration
    return_url = "devices:configuration_list"


class ConfigurationBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "devices.delete_configuration"
    model = Configuration
    filter = ConfigurationFilterSet
    table = ConfigurationTable


class PlatformList(PermissionRequiredMixin, ModelListView):
    permission_required = "devices.view_platform"
    queryset = Platform.objects.annotate(
        router_count=Count("router", distinct=True)
    ).order_by("name")
    table = PlatformTable
    template = "devices/platform/list.html"


class PlatformAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "devices.add_platform"
    model = Platform
    form = PlatformForm
    return_url = "devices:platform_list"
    template = "devices/platform/add_edit.html"


class PlatformEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "devices.change_platform"
    model = Platform
    form = PlatformForm
    template = "devices/platform/add_edit.html"


class PlatformDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "devices.delete_platform"
    model = Platform
    return_url = "devices:platform_list"


class PlatformBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "devices.delete_platform"
    model = Platform
    filter = PlatformFilterSet
    table = PlatformTable
