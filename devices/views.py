from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from extras.views import BulkEditView, ObjectConfigContextView
from net.models import Connection
from peering.filtersets import (
    DirectPeeringSessionFilterSet,
    InternetExchangePeeringSessionFilterSet,
)
from peering.forms import (
    DirectPeeringSessionFilterForm,
    InternetExchangePeeringSessionFilterForm,
)
from peering.models import DirectPeeringSession, InternetExchangePeeringSession
from peering.tables import (
    DirectPeeringSessionTable,
    InternetExchangePeeringSessionTable,
)
from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import PermissionRequiredMixin

from .filtersets import ConfigurationFilterSet, PlatformFilterSet, RouterFilterSet
from .forms import (
    ConfigurationFilterForm,
    ConfigurationForm,
    PlatformForm,
    RouterBulkEditForm,
    RouterFilterForm,
    RouterForm,
)
from .models import Configuration, Platform, Router
from .tables import (
    ConfigurationTable,
    PlatformTable,
    RouterConnectionTable,
    RouterTable,
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


class RouterList(ObjectListView):
    permission_required = "devices.view_router"
    queryset = (
        Router.objects.annotate(
            connection_count=Count("connection", distinct=True),
            directpeeringsession_count=Count("directpeeringsession", distinct=True),
            internetexchangepeeringsession_count=Count(
                "connection__internetexchangepeeringsession", distinct=True
            ),
        )
        .prefetch_related("configuration_template")
        .order_by("local_autonomous_system", "name")
    )
    filterset = RouterFilterSet
    filterset_form = RouterFilterForm
    table = RouterTable
    template_name = "devices/router/list.html"


class RouterView(ObjectView):
    permission_required = "devices.view_router"
    queryset = Router.objects.all()
    tab = "main"

    def get_extra_context(self, request, instance):
        return {"connections": Connection.objects.filter(router=instance)}


class RouterConfigContext(ObjectConfigContextView):
    permission_required = "devices.view_router"
    queryset = Router.objects.all()
    base_template = "devices/router/_base.html"


class RouterEdit(ObjectEditView):
    queryset = Router.objects.all()
    form = RouterForm


class RouterBulkEdit(BulkEditView):
    permission_required = "devices.change_router"
    queryset = Router.objects.all()
    filterset = RouterFilterSet
    table = RouterTable
    form = RouterBulkEditForm


class RouterDelete(ObjectDeleteView):
    permission_required = "devices.delete_router"
    queryset = Router.objects.all()


class RouterBulkDelete(BulkDeleteView):
    queryset = Router.objects.all()
    filterset = RouterFilterSet
    table = RouterTable


class RouterConfiguration(PermissionRequiredMixin, View):
    permission_required = "devices.view_router_configuration"
    tab = "configuration"

    def get(self, request, pk):
        instance = get_object_or_404(Router, pk=pk)

        if "raw" in request.GET:
            return HttpResponse(
                instance.render_configuration(), content_type="text/plain"
            )

        return render(
            request,
            "devices/router/configuration.html",
            {"instance": instance, "tab": self.tab},
        )


class RouterConnections(ObjectChildrenView):
    permission_required = ("devices.view_router", "net.view_connection")
    queryset = Router.objects.all()
    child_model = Connection
    table = RouterConnectionTable
    template_name = "devices/router/connections.html"
    tab = "connections"

    def get_children(self, request, parent):
        return Connection.objects.filter(router=parent)


class RouterDirectPeeringSessions(ObjectChildrenView):
    permission_required = ("devices.view_router", "peering.view_directpeeringsession")
    queryset = Router.objects.all()
    child_model = DirectPeeringSession
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template_name = "devices/router/direct_peering_sessions.html"
    tab = "direct-sessions"

    def get_children(self, request, parent):
        return parent.directpeeringsession_set.order_by("relationship", "ip_address")


class RouterInternetExchangesPeeringSessions(ObjectChildrenView):
    permission_required = "devices.view_router"
    queryset = Router.objects.all()
    child_model = InternetExchangePeeringSession
    filterset = InternetExchangePeeringSessionFilterSet
    filterset_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template_name = "devices/router/internet_exchange_peering_sessions.html"
    tab = "ixp-sessions"

    def get_children(self, request, parent):
        return InternetExchangePeeringSession.objects.filter(
            internet_exchange__router=parent
        ).order_by("internet_exchange", "ip_address")
