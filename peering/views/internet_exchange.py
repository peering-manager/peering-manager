from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import pluralize
from django.utils.text import slugify
from django.views.generic import View

from extras.views import ObjectConfigContextView
from net.filtersets import ConnectionFilterSet
from net.forms import ConnectionFilterForm
from net.models import Connection
from net.tables import ConnectionTable
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    GetReturnURLMixin,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
    PermissionRequiredMixin,
)
from peeringdb.filtersets import NetworkIXLanFilterSet
from peeringdb.forms import NetworkIXLanFilterForm
from peeringdb.tables import NetworkIXLanTable
from utils.forms import ConfirmationForm
from utils.functions import count_related
from utils.views import ViewTab, register_model_view

from ..filtersets import (
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
)
from ..forms import (
    InternetExchangeBulkEditForm,
    InternetExchangeFilterForm,
    InternetExchangeForm,
    InternetExchangePeeringSessionFilterForm,
)
from ..models import (
    AutonomousSystem,
    InternetExchange,
    InternetExchangePeeringSession,
    NetworkIXLan,
)
from ..tables import InternetExchangePeeringSessionTable, InternetExchangeTable

__all__ = (
    "InternetExchangeBulkDelete",
    "InternetExchangeBulkEdit",
    "InternetExchangeConfigContext",
    "InternetExchangeConnections",
    "InternetExchangeDelete",
    "InternetExchangeEdit",
    "InternetExchangeIXAPI",
    "InternetExchangeList",
    "InternetExchangePeeringDBImport",
    "InternetExchangePeeringSessions",
    "InternetExchangePeers",
    "InternetExchangeView",
)


@register_model_view(InternetExchange, name="list", path="", detail=False)
class InternetExchangeList(ObjectListView):
    permission_required = "peering.view_internetexchange"
    queryset = (
        InternetExchange.objects.all()
        .order_by("local_autonomous_system", "name", "slug")
        .annotate(
            connection_count=count_related(Connection, "internet_exchange_point"),
            session_count=count_related(
                InternetExchangePeeringSession,
                "ixp_connection__internet_exchange_point",
            ),
        )
    )
    table = InternetExchangeTable
    filterset = InternetExchangeFilterSet
    filterset_form = InternetExchangeFilterForm
    template_name = "peering/internetexchange/list.html"


@register_model_view(InternetExchange)
class InternetExchangeView(ObjectView):
    permission_required = "peering.view_internetexchange"
    queryset = InternetExchange.objects.all()

    def get_extra_context(self, request, instance):
        if not instance.linked_to_peeringdb:
            # Try fixing the PeeringDB record references if possible
            ix = instance.link_to_peeringdb()
            if ix:
                messages.info(
                    request,
                    "PeeringDB record for this IX was invalid, it's been fixed.",
                )

        return {}


@register_model_view(model=InternetExchange, name="add", detail=False)
@register_model_view(model=InternetExchange, name="edit")
class InternetExchangeEdit(ObjectEditView):
    queryset = InternetExchange.objects.all()
    form = InternetExchangeForm


@register_model_view(InternetExchange, name="delete")
class InternetExchangeDelete(ObjectDeleteView):
    permission_required = "peering.delete_internetexchange"
    queryset = InternetExchange.objects.all()


@register_model_view(InternetExchange, name="bulk_edit", path="edit", detail=False)
class InternetExchangeBulkEdit(BulkEditView):
    permission_required = "peering.change_internetexchange"
    queryset = InternetExchange.objects.all()
    filterset = InternetExchangeFilterSet
    table = InternetExchangeTable
    form = InternetExchangeBulkEditForm


@register_model_view(InternetExchange, name="bulk_delete", path="delete", detail=False)
class InternetExchangeBulkDelete(BulkDeleteView):
    queryset = InternetExchange.objects.all()
    filterset = InternetExchangeFilterSet
    table = InternetExchangeTable


@register_model_view(InternetExchange, name="configcontext", path="config-context")
class InternetExchangeConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_internetexchange"
    queryset = InternetExchange.objects.all()
    base_template = "peering/internetexchange/_base.html"


@register_model_view(InternetExchange, name="connections")
class InternetExchangeConnections(ObjectChildrenView):
    permission_required = ("net.view_connection", "peering.view_internetexchange")
    queryset = InternetExchange.objects.all()
    child_model = Connection
    table = ConnectionTable
    filterset = ConnectionFilterSet
    filterset_form = ConnectionFilterForm
    template_name = "peering/internetexchange/connections.html"
    tab = ViewTab(
        label="Connections",
        badge=lambda instance: instance.get_connections().count(),
        permission="peering.view_connection",
    )

    def get_children(self, request, parent):
        return Connection.objects.filter(internet_exchange_point=parent)


@register_model_view(InternetExchange, name="peering_sessions", path="peering-sessions")
class InternetExchangePeeringSessions(ObjectChildrenView):
    permission_required = (
        "peering.view_internetexchange",
        "peering.view_internetexchangepeeringsession",
    )
    queryset = InternetExchange.objects.all()
    child_model = InternetExchangePeeringSession
    filterset = InternetExchangePeeringSessionFilterSet
    filterset_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template_name = "peering/internetexchange/sessions.html"
    tab = ViewTab(
        label="Peering Sessions",
        badge=lambda instance: instance.get_peering_sessions().count(),
        permission="peering.view_internetexchangepeeringsession",
        weight=2000,
    )

    def get_children(self, request, parent):
        return parent.get_peering_sessions()


@register_model_view(InternetExchange, name="peers")
class InternetExchangePeers(ObjectChildrenView):
    permission_required = "peering.view_internetexchange"
    queryset = InternetExchange.objects.all()
    child_model = NetworkIXLan
    filterset = NetworkIXLanFilterSet
    filterset_form = NetworkIXLanFilterForm
    table = NetworkIXLanTable
    template_name = "peering/internetexchange/peers.html"
    tab = ViewTab(label="Available Peers", weight=3000)

    def get_children(self, request, parent):
        return parent.get_available_peers()

    def get_extra_context(self, request, instance):
        return {"hidden_peers": instance.get_hidden_peers()}


@register_model_view(InternetExchange, name="ixapi")
class InternetExchangeIXAPI(PermissionRequiredMixin, View):
    permission_required = "peering.view_internet_exchange_point_ixapi"
    tab = ViewTab(
        label="IX-API",
        permission="peering.view_internet_exchange_point_ixapi",
        weight=4000,
    )

    def get(self, request, pk):
        instance = get_object_or_404(InternetExchange, pk=pk)
        try:
            return render(
                request,
                "peering/internetexchange/ixapi.html",
                {
                    "tab": self.tab,
                    "instance": instance,
                    "ixapi_service": instance.get_ixapi_network_service(),
                },
            )
        except Exception as e:
            return render(
                request,
                "peering/internetexchange/ixapi_error.html",
                {"tab": self.tab, "instance": instance, "error": str(e)},
            )


@register_model_view(
    InternetExchange, name="peeringdb_import", path="peeringdb-import", detail=False
)
class InternetExchangePeeringDBImport(GetReturnURLMixin, PermissionRequiredMixin, View):
    permission_required = "peering.add_internetexchange"
    default_return_url = "peering:internetexchange_list"

    def get_missing_ixps(self, request):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            messages.error(
                request, "Unable to import IXPs and connections without affiliated AS."
            )
            return redirect(self.get_return_url(request))

        # Get known IXPs and their connections
        netixlans = Connection.objects.filter(
            peeringdb_netixlan__isnull=False
        ).values_list("peeringdb_netixlan", flat=True)
        # Find missing connections
        missing_netixlans = NetworkIXLan.objects.filter(asn=affiliated.asn).exclude(
            pk__in=netixlans
        )

        # Map missing IXPs based on missing connections
        missing_ixps = {}
        for netixlan in missing_netixlans:
            ixlan = missing_ixps.setdefault(netixlan.ixlan, [])
            ixlan.append(netixlan)

        return affiliated, missing_ixps

    @transaction.atomic
    def import_ixps(self, local_as, missing_ixps):
        """
        Imports IXPs and connections in a single database transaction.
        """
        imported_ixps, imported_connections = 0, 0

        if not missing_ixps:
            return imported_ixps, imported_connections

        for ixp, connections in missing_ixps.items():
            i, created = InternetExchange.objects.get_or_create(
                slug=slugify(f"{ixp.ix.name} {ixp.ix.pk}"),
                defaults={
                    "peeringdb_ixlan": ixp,
                    "local_autonomous_system": local_as,
                    "name": ixp.ix.name,
                },
            )

            for connection in connections:
                if not connection.cidr4 and not connection.cidr6:
                    # PeeringDB has no address data; skip!
                    continue
                Connection.objects.create(
                    peeringdb_netixlan=connection,
                    internet_exchange_point=i,
                    ipv4_address=connection.cidr4,
                    ipv6_address=connection.cidr6,
                )
                imported_connections += 1

            if created:
                imported_ixps += 1

        return imported_ixps, imported_connections

    def get(self, request):
        _, missing_ixps = self.get_missing_ixps(request)

        if not missing_ixps:
            messages.warning(request, "No IXPs nor connections to import.")
            return redirect(self.get_return_url(request))

        return render(
            request,
            "peering/internetexchange/import.html",
            {
                "form": ConfirmationForm(initial=request.GET),
                "missing_ixps": missing_ixps,
                "return_url": self.get_return_url(request),
            },
        )

    def post(self, request):
        local_as, missing_ixps = self.get_missing_ixps(request)
        form = ConfirmationForm(request.POST)

        if form.is_valid():
            ixp_number, connection_number = self.import_ixps(local_as, missing_ixps)

            if ixp_number == 0 and connection_number == 0:
                messages.warning(request, "No IXPs imported.")
            else:
                message = ["Imported"]
                if ixp_number > 0:
                    message.append(f"{ixp_number} IXP{pluralize(ixp_number)}")
                if connection_number > 0:
                    message.append(
                        f"{connection_number} connection{pluralize(connection_number)}"
                    )
                messages.success(request, f"{' '.join(message)}.")

        return redirect(self.get_return_url(request))
