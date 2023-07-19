from django.db.models import Count

from peering.models import Router
from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)

from .filtersets import ConfigurationFilterSet, PlatformFilterSet
from .forms import ConfigurationFilterForm, ConfigurationForm, PlatformForm
from .models import Configuration, Platform
from .tables import ConfigurationTable, PlatformTable


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
    tab = "main"

    def get_extra_context(self, request, instance):
        return {"routers": Router.objects.filter(configuration_template=instance)}


class ConfigurationEdit(ObjectEditView):
    queryset = Configuration.objects.all()
    form = ConfigurationForm


class ConfigurationDelete(ObjectDeleteView):
    permission_required = "devices.delete_configuration"
    queryset = Configuration.objects.all()


class ConfigurationBulkDelete(BulkDeleteView):
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


class PlatformEdit(ObjectEditView):
    queryset = Platform.objects.all()
    form = PlatformForm


class PlatformDelete(ObjectDeleteView):
    permission_required = "devices.delete_platform"
    queryset = Platform.objects.all()


class PlatformBulkDelete(BulkDeleteView):
    queryset = Platform.objects.all()
    filterset = PlatformFilterSet
    table = PlatformTable
