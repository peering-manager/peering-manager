from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import ConfigurationFilterSet
from ..forms import (
    ConfigurationFilterForm,
    ConfigurationForm,
)
from ..models import Configuration, Router
from ..tables import ConfigurationTable

__all__ = (
    "ConfigurationBulkDelete",
    "ConfigurationDelete",
    "ConfigurationEdit",
    "ConfigurationList",
    "ConfigurationView",
)


@register_model_view(model=Configuration, name="list", path="", detail=False)
class ConfigurationList(ObjectListView):
    permission_required = "devices.view_configuration"
    queryset = Configuration.objects.all()
    filterset = ConfigurationFilterSet
    filterset_form = ConfigurationFilterForm
    table = ConfigurationTable
    template_name = "devices/configuration/list.html"


@register_model_view(model=Configuration)
class ConfigurationView(ObjectView):
    permission_required = "devices.view_configuration"
    queryset = Configuration.objects.all()

    def get_extra_context(self, request, instance):
        return {"routers": Router.objects.filter(configuration_template=instance)}


@register_model_view(model=Configuration, name="add", detail=False)
@register_model_view(model=Configuration, name="edit")
class ConfigurationEdit(ObjectEditView):
    queryset = Configuration.objects.all()
    form = ConfigurationForm


@register_model_view(model=Configuration, name="delete")
class ConfigurationDelete(ObjectDeleteView):
    permission_required = "devices.delete_configuration"
    queryset = Configuration.objects.all()


@register_model_view(
    model=Configuration, name="bulk_delete", path="delete", detail=False
)
class ConfigurationBulkDelete(BulkDeleteView):
    queryset = Configuration.objects.all()
    filterset = ConfigurationFilterSet
    table = ConfigurationTable
