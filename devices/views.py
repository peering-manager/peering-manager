from django.db.models import Count

from utils.views import (
    AddOrEditView,
    BulkDeleteView,
    DeleteView,
    ModelListView,
    PermissionRequiredMixin,
)

from .filters import PlatformFilterSet
from .forms import PlatformForm
from .models import Platform
from .tables import PlatformTable


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
