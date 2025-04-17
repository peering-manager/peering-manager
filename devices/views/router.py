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
from utils.views import PermissionRequiredMixin, register_model_view

from ..filtersets import RouterFilterSet
from ..forms import RouterBulkEditForm, RouterFilterForm, RouterForm
from ..models import Router
from ..tables import RouterConnectionTable, RouterTable

__all__ = (
    "RouterBulkDelete",
    "RouterBulkEdit",
    "RouterConfigContext",
    "RouterConfiguration",
    "RouterConnections",
    "RouterDelete",
    "RouterDirectPeeringSessions",
    "RouterEdit",
    "RouterInternetExchangesPeeringSessions",
    "RouterList",
    "RouterView",
)


@register_model_view(model=Router, name="list", path="", detail=False)
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


@register_model_view(model=Router)
class RouterView(ObjectView):
    permission_required = "devices.view_router"
    queryset = Router.objects.all()
    tab = "main"

    def get_extra_context(self, request, instance):
        return {"connections": Connection.objects.filter(router=instance)}


@register_model_view(model=Router, name="add", detail=False)
@register_model_view(model=Router, name="edit")
class RouterEdit(ObjectEditView):
    queryset = Router.objects.all()
    form = RouterForm


@register_model_view(model=Router, name="delete")
class RouterDelete(ObjectDeleteView):
    permission_required = "devices.delete_router"
    queryset = Router.objects.all()


@register_model_view(model=Router, name="bulk_edit", path="edit", detail=False)
class RouterBulkEdit(BulkEditView):
    permission_required = "devices.change_router"
    queryset = Router.objects.all()
    filterset = RouterFilterSet
    table = RouterTable
    form = RouterBulkEditForm


@register_model_view(model=Router, name="bulk_delete", path="delete", detail=False)
class RouterBulkDelete(BulkDeleteView):
    queryset = Router.objects.all()
    filterset = RouterFilterSet
    table = RouterTable


@register_model_view(model=Router, name="configcontext", path="config-context")
class RouterConfigContext(ObjectConfigContextView):
    permission_required = "devices.view_router"
    queryset = Router.objects.all()
    base_template = "devices/router/_base.html"


@register_model_view(model=Router, name="configuration", path="configuration")
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


@register_model_view(model=Router, name="connections", path="connections")
class RouterConnections(ObjectChildrenView):
    permission_required = ("devices.view_router", "net.view_connection")
    queryset = Router.objects.all()
    child_model = Connection
    table = RouterConnectionTable
    template_name = "devices/router/connections.html"
    tab = "connections"

    def get_children(self, request, parent):
        return Connection.objects.filter(router=parent)


@register_model_view(
    model=Router, name="direct_peering_sessions", path="direct-peering-sessions"
)
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


@register_model_view(
    model=Router, name="internet_exchange_peering_sessions", path="ix-peering-sessions"
)
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
