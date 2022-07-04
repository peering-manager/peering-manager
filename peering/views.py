from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import pluralize
from django.utils.text import slugify
from django.views.generic import View

from extras.views import ObjectConfigContextView
from net.filters import ConnectionFilterSet
from net.forms import ConnectionFilterForm
from net.models import Connection
from net.tables import ConnectionTable
from peering_manager.views.generics import (
    BulkDeleteView,
    BulkEditView,
    GetReturnURLMixin,
    ImportFromObjectView,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
    PermissionRequiredMixin,
)
from peeringdb.filters import NetworkIXLanFilterSet
from peeringdb.forms import NetworkIXLanFilterForm
from peeringdb.models import NetworkContact, NetworkIXLan
from peeringdb.tables import NetworkContactTable, NetworkIXLanTable
from utils.forms import ConfirmationForm
from utils.functions import count_related

from .filters import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    CommunityFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
    RouterFilterSet,
    RoutingPolicyFilterSet,
)
from .forms import (
    AutonomousSystemEmailForm,
    AutonomousSystemFilterForm,
    AutonomousSystemForm,
    BGPGroupBulkEditForm,
    BGPGroupFilterForm,
    BGPGroupForm,
    CommunityBulkEditForm,
    CommunityFilterForm,
    CommunityForm,
    DirectPeeringSessionBulkEditForm,
    DirectPeeringSessionFilterForm,
    DirectPeeringSessionForm,
    InternetExchangeBulkEditForm,
    InternetExchangeFilterForm,
    InternetExchangeForm,
    InternetExchangePeeringSessionBulkEditForm,
    InternetExchangePeeringSessionFilterForm,
    InternetExchangePeeringSessionForm,
    RouterBulkEditForm,
    RouterFilterForm,
    RouterForm,
    RoutingPolicyBulkEditForm,
    RoutingPolicyFilterForm,
    RoutingPolicyForm,
)
from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from .tables import (
    AutonomousSystemTable,
    BGPGroupTable,
    CommunityTable,
    DirectPeeringSessionTable,
    InternetExchangePeeringSessionTable,
    InternetExchangeTable,
    RouterConnectionTable,
    RouterTable,
    RoutingPolicyTable,
)


class AutonomousSystemList(ObjectListView):
    permission_required = "peering.view_autonomoussystem"
    queryset = (
        AutonomousSystem.objects.defer("prefixes")
        .annotate(
            directpeeringsession_count=Count("directpeeringsession", distinct=True),
            internetexchangepeeringsession_count=Count(
                "internetexchangepeeringsession", distinct=True
            ),
        )
        .order_by("affiliated", "asn")
    )
    filterset = AutonomousSystemFilterSet
    filterset_form = AutonomousSystemFilterForm
    table = AutonomousSystemTable
    template_name = "peering/autonomoussystem/list.html"


class AutonomousSystemView(ObjectView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")

    def get_extra_context(self, request, instance):
        shared_internet_exchanges = {}

        if not request.user.is_anonymous and request.user.preferences.get("context.as"):
            try:
                affiliated = AutonomousSystem.objects.get(
                    pk=request.user.preferences.get("context.as")
                )
            except AutonomousSystem.DoesNotExist:
                affiliated = None

            for ix in instance.get_shared_internet_exchange_points(affiliated):
                shared_internet_exchanges[ix] = instance.get_missing_peering_sessions(
                    affiliated, ix
                )

        return {
            "shared_internet_exchanges": shared_internet_exchanges,
            "active_tab": "main",
        }


class AutonomousSystemConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    base_template = "peering/autonomoussystem/_base.html"


class AutonomousSystemAdd(ObjectEditView):
    permission_required = "peering.add_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    model_form = AutonomousSystemForm
    template_name = "peering/autonomoussystem/add_edit.html"


class AutonomousSystemEdit(ObjectEditView):
    permission_required = "peering.change_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    model_form = AutonomousSystemForm
    template_name = "peering/autonomoussystem/add_edit.html"


class AutonomousSystemDelete(ObjectDeleteView):
    permission_required = "peering.delete_autonomoussystem"
    queryset = AutonomousSystem.objects.all()


class AutonomousSystemBulkDelete(BulkDeleteView):
    permission_required = "peering.delete_autonomoussystem"
    queryset = AutonomousSystem.objects.all()
    filterset = AutonomousSystemFilterSet
    table = AutonomousSystemTable


class AutonomousSystemPeeringDB(ObjectChildrenView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    child_model = NetworkContact
    table = NetworkContactTable
    template_name = "peering/autonomoussystem/peeringdb.html"

    def get_children(self, request, parent):
        return parent.peeringdb_contacts

    def get_extra_context(self, request, instance):
        return {"active_tab": "peeringdb"}


class AutonomousSystemDirectPeeringSessions(ObjectChildrenView):
    permission_required = (
        "peering.view_autonomoussystem",
        "peering.view_directpeeringsession",
    )
    queryset = AutonomousSystem.objects.defer("prefixes")
    child_model = DirectPeeringSession
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template_name = "peering/autonomoussystem/direct_peering_sessions.html"

    def get_children(self, request, parent):
        return (
            parent.get_direct_peering_sessions()
            .prefetch_related("bgp_group")
            .order_by("bgp_group", "relationship", "ip_address")
        )

    def get_extra_context(self, request, instance):
        return {"active_tab": "directsessions"}


class AutonomousSystemInternetExchangesPeeringSessions(ObjectChildrenView):
    permission_required = (
        "peering.view_autonomoussystem",
        "peering.view_internetexchangepeeringsession",
    )
    queryset = AutonomousSystem.objects.defer("prefixes")
    child_model = InternetExchangePeeringSession
    filterset = InternetExchangePeeringSessionFilterSet
    filterset_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template_name = "peering/autonomoussystem/internet_exchange_peering_sessions.html"

    def get_children(self, request, parent):
        return (
            parent.get_ixp_peering_sessions()
            .prefetch_related("ixp_connection")
            .order_by("ixp_connection", "ip_address")
        )

    def get_extra_context(self, request, instance):
        return {"active_tab": "ixp-sessions"}


class AutonomousSystemPeers(ObjectChildrenView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    child_model = NetworkIXLan
    table = NetworkIXLanTable
    template_name = "peering/autonomoussystem/peers.html"

    def get_children(self, request, parent):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            affiliated = None

        return parent.get_missing_peering_sessions(affiliated)

    def get_extra_context(self, request, instance):
        return {"active_tab": "peers"}


class AutonomousSystemEmail(PermissionRequiredMixin, View):
    permission_required = "peering.send_email"

    def get(self, request, *args, **kwargs):
        instance = get_object_or_404(AutonomousSystem, pk=kwargs["pk"])

        if not instance.can_receive_email:
            return redirect(instance.get_absolute_url())

        form = AutonomousSystemEmailForm()
        form.fields["recipient"].choices = instance.get_contact_email_addresses()
        form.fields["cc"].choices = instance.get_cc_email_contacts()
        return render(
            request,
            "peering/autonomoussystem/email.html",
            {"instance": instance, "form": form, "active_tab": "email"},
        )

    def post(self, request, *args, **kwargs):
        instance = get_object_or_404(AutonomousSystem, pk=kwargs["pk"])

        if not instance.can_receive_email:
            redirect(instance.get_absolute_url())

        form = AutonomousSystemEmailForm(request.POST)
        form.fields["recipient"].choices = instance.get_contact_email_addresses()
        form.fields["cc"].choices = instance.get_cc_email_contacts()

        if form.is_valid():
            mail = EmailMessage(
                subject=form.cleaned_data["subject"],
                body=form.cleaned_data["body"],
                from_email=settings.SERVER_EMAIL,
                to=form.cleaned_data["recipient"],
                cc=form.cleaned_data["cc"],
            )
            sent = mail.send()
            if sent == 1:
                messages.success(request, "Email sent.")
            else:
                messages.error(request, "Unable to send the email.")

        return redirect(instance.get_absolute_url())


class BGPGroupList(ObjectListView):
    permission_required = "peering.view_bgpgroup"
    queryset = BGPGroup.objects.annotate(
        directpeeringsession_count=Count("directpeeringsession")
    ).order_by("name", "slug")
    filterset = BGPGroupFilterSet
    filterset_form = BGPGroupFilterForm
    table = BGPGroupTable
    template_name = "peering/bgpgroup/list.html"


class BGPGroupView(ObjectView):
    permission_required = "peering.view_bgpgroup"
    queryset = BGPGroup.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class BGPGroupConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_bgpgroup"
    queryset = BGPGroup.objects.all()
    base_template = "peering/bgpgroup/_base.html"


class BGPGroupAdd(ObjectEditView):
    permission_required = "peering.add_bgpgroup"
    queryset = BGPGroup.objects.all()
    model_form = BGPGroupForm
    template_name = "peering/bgpgroup/add_edit.html"


class BGPGroupEdit(ObjectEditView):
    permission_required = "peering.change_bgpgroup"
    queryset = BGPGroup.objects.all()
    model_form = BGPGroupForm
    template_name = "peering/bgpgroup/add_edit.html"


class BGPGroupBulkEdit(BulkEditView):
    permission_required = "peering.change_bgpgroup"
    queryset = BGPGroup.objects.all()
    filterset = BGPGroupFilterSet
    table = BGPGroupTable
    form = BGPGroupBulkEditForm


class BGPGroupDelete(ObjectDeleteView):
    permission_required = "peering.delete_bgpgroup"
    queryset = BGPGroup.objects.all()


class BGPGroupBulkDelete(BulkDeleteView):
    permission_required = "peering.delete_bgpgroup"
    queryset = BGPGroup.objects.all()
    filterset = BGPGroupFilterSet
    table = BGPGroupTable


class BGPGroupPeeringSessions(ObjectChildrenView):
    permission_required = ("peering.view_bgpgroup", "peering.view_directpeeringsession")
    queryset = BGPGroup.objects.all()
    child_model = DirectPeeringSession
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template_name = "peering/bgpgroup/sessions.html"

    def get_children(self, request, parent):
        return parent.directpeeringsession_set.prefetch_related(
            "autonomous_system", "router"
        ).order_by("autonomous_system", "ip_address")

    def get_extra_context(self, request, instance):
        return {"active_tab": "directsessions"}


class CommunityList(ObjectListView):
    permission_required = "peering.view_community"
    queryset = Community.objects.all()
    filterset = CommunityFilterSet
    filterset_form = CommunityFilterForm
    table = CommunityTable
    template_name = "peering/community/list.html"


class CommunityView(ObjectView):
    permission_required = "peering.view_community"
    queryset = Community.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class CommunityConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_community"
    queryset = Community.objects.all()
    base_template = "peering/community/_base.html"


class CommunityAdd(ObjectEditView):
    permission_required = "peering.add_community"
    queryset = Community.objects.all()
    model_form = CommunityForm
    template_name = "peering/community/add_edit.html"


class CommunityEdit(ObjectEditView):
    permission_required = "peering.change_community"
    queryset = Community.objects.all()
    model_form = CommunityForm
    template_name = "peering/community/add_edit.html"


class CommunityDelete(ObjectDeleteView):
    permission_required = "peering.delete_community"
    queryset = Community.objects.all()


class CommunityBulkDelete(BulkDeleteView):
    permission_required = "peering.delete_community"
    queryset = Community.objects.all()
    filterset = CommunityFilterSet
    table = CommunityTable


class CommunityBulkEdit(BulkEditView):
    permission_required = "peering.change_community"
    queryset = Community.objects.all()
    filterset = CommunityFilterSet
    table = CommunityTable
    form = CommunityBulkEditForm


class DirectPeeringSessionList(ObjectListView):
    permission_required = "peering.view_directpeeringsession"
    queryset = DirectPeeringSession.objects.order_by(
        "local_autonomous_system", "autonomous_system", "ip_address"
    )
    table = DirectPeeringSessionTable
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    template_name = "peering/directpeeringsession/list.html"


class DirectPeeringSessionView(ObjectView):
    permission_required = "peering.view_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class DirectPeeringSessionConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()
    base_template = "peering/directpeeringsession/_base.html"


class DirectPeeringSessionAdd(ObjectEditView):
    permission_required = "peering.add_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()
    model_form = DirectPeeringSessionForm
    template_name = "peering/directpeeringsession/add_edit.html"


class DirectPeeringSessionEdit(ObjectEditView):
    permission_required = "peering.change_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()
    model_form = DirectPeeringSessionForm
    template_name = "peering/directpeeringsession/add_edit.html"


class DirectPeeringSessionBulkEdit(BulkEditView):
    permission_required = "peering.change_directpeeringsession"
    queryset = DirectPeeringSession.objects.select_related("autonomous_system")
    filterset = DirectPeeringSessionFilterSet
    table = DirectPeeringSessionTable
    form = DirectPeeringSessionBulkEditForm


class DirectPeeringSessionDelete(ObjectDeleteView):
    permission_required = "peering.delete_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()


class DirectPeeringSessionBulkDelete(BulkDeleteView):
    permission_required = "peering.delete_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()
    filterset = DirectPeeringSessionFilterSet
    table = DirectPeeringSessionTable


class InternetExchangeList(ObjectListView):
    permission_required = "peering.view_internetexchange"
    queryset = (
        InternetExchange.objects.all()
        .order_by("local_autonomous_system", "name", "slug")
        .annotate(connection_count=count_related(Connection, "internet_exchange_point"))
    )
    table = InternetExchangeTable
    filterset = InternetExchangeFilterSet
    filterset_form = InternetExchangeFilterForm
    template_name = "peering/internetexchange/list.html"


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

        return {"active_tab": "main"}


class InternetExchangeConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_internetexchange"
    queryset = InternetExchange.objects.all()
    base_template = "peering/internetexchange/_base.html"


class InternetExchangeAdd(ObjectEditView):
    permission_required = "peering.add_internetexchange"
    queryset = InternetExchange.objects.all()
    model_form = InternetExchangeForm
    template_name = "peering/internetexchange/add_edit.html"


class InternetExchangeEdit(ObjectEditView):
    permission_required = "peering.change_internetexchange"
    queryset = InternetExchange.objects.all()
    model_form = InternetExchangeForm
    template_name = "peering/internetexchange/add_edit.html"


class InternetExchangeBulkEdit(BulkEditView):
    permission_required = "peering.change_internetexchange"
    queryset = InternetExchange.objects.all()
    filterset = InternetExchangeFilterSet
    table = InternetExchangeTable
    form = InternetExchangeBulkEditForm


class InternetExchangeDelete(ObjectDeleteView):
    permission_required = "peering.delete_internetexchange"
    queryset = InternetExchange.objects.all()


class InternetExchangeBulkDelete(BulkDeleteView):
    permission_required = "peering.delete_internetexchange"
    queryset = InternetExchange.objects.all()
    filterset = InternetExchangeFilterSet
    table = InternetExchangeTable


class InternetExchangeConnections(ObjectChildrenView):
    permission_required = ("net.view_connection", "peering.view_internetexchange")
    queryset = InternetExchange.objects.all()
    child_model = Connection
    table = ConnectionTable
    filterset = ConnectionFilterSet
    filterset_form = ConnectionFilterForm
    template_name = "peering/internetexchange/connections.html"

    def get_children(self, request, parent):
        return Connection.objects.filter(internet_exchange_point=parent)

    def get_extra_context(self, request, instance):
        return {"active_tab": "connections"}


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

    def get_children(self, request, parent):
        return parent.get_peering_sessions()

    def get_extra_context(self, request, instance):
        return {"active_tab": "sessions"}


class InternetExchangePeers(ObjectChildrenView):
    permission_required = "peering.view_internetexchange"
    queryset = InternetExchange.objects.all()
    child_model = NetworkIXLan
    filterset = NetworkIXLanFilterSet
    filterset_form = NetworkIXLanFilterForm
    table = NetworkIXLanTable
    template_name = "peering/internetexchange/peers.html"

    def get_children(self, request, parent):
        return parent.get_available_peers()

    def get_extra_context(self, request, instance):
        return {"active_tab": "peers", "internet_exchange_id": instance.pk}


class InternetExchangeIXAPI(PermissionRequiredMixin, View):
    permission_required = "peering.view_internet_exchange_point_ixapi"

    def get(self, request, pk):
        instance = get_object_or_404(InternetExchange, pk=pk)
        try:
            return render(
                request,
                "peering/internetexchange/ixapi.html",
                {
                    "instance": instance,
                    "ixapi_service": instance.get_ixapi_network_service(),
                    "active_tab": "ixapi",
                },
            )
        except Exception as e:
            return render(
                request,
                "peering/internetexchange/ixapi_error.html",
                {"instance": instance, "error": str(e), "active_tab": "ixapi"},
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


class InternetExchangePeeringSessionList(ObjectListView):
    permission_required = "peering.view_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.order_by(
        "autonomous_system", "ip_address"
    )
    table = InternetExchangePeeringSessionTable
    filterset = InternetExchangePeeringSessionFilterSet
    filterset_form = InternetExchangePeeringSessionFilterForm
    template_name = "peering/internetexchangepeeringsession/list.html"


class InternetExchangePeeringSessionView(ObjectView):
    permission_required = "peering.view_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()

    def get_extra_context(self, request, instance):
        return {"is_abandoned": instance.is_abandoned(), "active_tab": "main"}


class InternetExchangePeeringSessionConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()
    base_template = "peering/internetexchangepeeringsession/_base.html"


class InternetExchangePeeringSessionAdd(ObjectEditView):
    permission_required = "peering.add_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()
    model_form = InternetExchangePeeringSessionForm
    template_name = "peering/internetexchangepeeringsession/add_edit.html"


class InternetExchangePeeringSessionEdit(ObjectEditView):
    permission_required = "peering.change_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()
    model_form = InternetExchangePeeringSessionForm
    template_name = "peering/internetexchangepeeringsession/add_edit.html"


class InternetExchangePeeringSessionBulkEdit(BulkEditView):
    permission_required = "peering.change_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.select_related(
        "autonomous_system"
    )
    filterset = InternetExchangePeeringSessionFilterSet
    table = InternetExchangePeeringSessionTable
    form = InternetExchangePeeringSessionBulkEditForm


class InternetExchangePeeringSessionDelete(ObjectDeleteView):
    permission_required = "peering.delete_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()


class InternetExchangePeeringSessionBulkDelete(BulkDeleteView):
    permission_required = "peering.delete_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()
    filterset = InternetExchangePeeringSessionFilterSet
    table = InternetExchangePeeringSessionTable


class InternetExchangePeeringSessionImportFromPeeringDB(ImportFromObjectView):
    permission_required = "peering.add_internetexchangepeeringsession"
    queryset = NetworkIXLan.objects.all()
    form_model = InternetExchangePeeringSessionForm
    template_name = "peering/internetexchangepeeringsession/add_from_peeringdb.html"

    def process_base_object(self, request, base):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            return []

        ixp = None
        if "internet_exchange_id" in request.POST:
            ixp = InternetExchange.objects.get(
                pk=request.POST.get("internet_exchange_id")
            )

        return InternetExchangePeeringSession.create_from_peeringdb(
            affiliated, ixp, base
        )

    def sort_objects(self, object_list):
        objects = []
        for object_couple in object_list:
            for o in object_couple:
                if o:
                    objects.append(
                        {
                            "autonomous_system": o.autonomous_system,
                            "ixp_connection": o.ixp_connection,
                            "ip_address": o.ip_address,
                        }
                    )
        return objects


class RouterList(ObjectListView):
    permission_required = "peering.view_router"
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
    template_name = "peering/router/list.html"


class RouterView(ObjectView):
    permission_required = "peering.view_router"
    queryset = Router.objects.all()

    def get_extra_context(self, request, instance):
        return {
            "connections": Connection.objects.filter(router=instance),
            "active_tab": "main",
        }


class RouterConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_router"
    queryset = Router.objects.all()
    base_template = "peering/router/_base.html"


class RouterAdd(ObjectEditView):
    permission_required = "peering.add_router"
    queryset = Router.objects.all()
    model_form = RouterForm
    template_name = "peering/router/add_edit.html"


class RouterEdit(ObjectEditView):
    permission_required = "peering.change_router"
    queryset = Router.objects.all()
    model_form = RouterForm
    template_name = "peering/router/add_edit.html"


class RouterBulkEdit(BulkEditView):
    permission_required = "peering.change_router"
    queryset = Router.objects.all()
    filterset = RouterFilterSet
    table = RouterTable
    form = RouterBulkEditForm


class RouterDelete(ObjectDeleteView):
    permission_required = "peering.delete_router"
    queryset = Router.objects.all()


class RouterBulkDelete(BulkDeleteView):
    permission_required = "peering.delete_router"
    queryset = Router.objects.all()
    filterset = RouterFilterSet
    table = RouterTable


class RouterConfiguration(PermissionRequiredMixin, View):
    permission_required = "peering.view_router_configuration"

    def get(self, request, pk):
        instance = get_object_or_404(Router, pk=pk)

        if "raw" in request.GET:
            return HttpResponse(
                instance.generate_configuration(), content_type="text/plain"
            )

        return render(
            request,
            "peering/router/configuration.html",
            {"instance": instance, "active_tab": "configuration"},
        )


class RouterConnections(ObjectChildrenView):
    permission_required = ("peering.view_router", "net.view_connection")
    queryset = Router.objects.all()
    child_model = Connection
    table = RouterConnectionTable
    template_name = "peering/router/connections.html"

    def get_children(self, request, parent):
        return Connection.objects.filter(router=parent)

    def get_extra_context(self, request, instance):
        return {"active_tab": "connections"}


class RouterDirectPeeringSessions(ObjectChildrenView):
    permission_required = ("peering.view_router", "peering.view_directpeeringsession")
    queryset = Router.objects.all()
    child_model = DirectPeeringSession
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template_name = "peering/router/direct_peering_sessions.html"

    def get_children(self, request, parent):
        return parent.directpeeringsession_set.order_by("relationship", "ip_address")

    def get_extra_context(self, request, instance):
        return {"active_tab": "directsessions"}


class RouterInternetExchangesPeeringSessions(ObjectChildrenView):
    permission_required = "peering.view_router"
    queryset = Router.objects.all()
    child_model = InternetExchangePeeringSession
    filterset = InternetExchangePeeringSessionFilterSet
    filterset_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template_name = "peering/router/internet_exchange_peering_sessions.html"

    def get_children(self, request, parent):
        return InternetExchangePeeringSession.objects.filter(
            internet_exchange__router=parent
        ).order_by("internet_exchange", "ip_address")

    def get_extra_context(self, request, instance):
        return {"active_tab": "ixp-sessions"}


class RoutingPolicyList(ObjectListView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    filterset_form = RoutingPolicyFilterForm
    table = RoutingPolicyTable
    template_name = "peering/routingpolicy/list.html"


class RoutingPolicyView(ObjectView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()

    def get_extra_context(self, request, instance):
        return {"active_tab": "main"}


class RoutingPolicyContext(ObjectConfigContextView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    base_template = "peering/routingpolicy/_base.html"


class RoutingPolicyAdd(ObjectEditView):
    permission_required = "peering.add_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    model_form = RoutingPolicyForm
    template_name = "peering/routingpolicy/add_edit.html"


class RoutingPolicyEdit(ObjectEditView):
    permission_required = "peering.change_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    model_form = RoutingPolicyForm
    template_name = "peering/routingpolicy/add_edit.html"


class RoutingPolicyBulkEdit(BulkEditView):
    permission_required = "peering.change_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    table = RoutingPolicyTable
    form = RoutingPolicyBulkEditForm


class RoutingPolicyDelete(ObjectDeleteView):
    permission_required = "peering.delete_routingpolicy"
    queryset = RoutingPolicy.objects.all()


class RoutingPolicyBulkDelete(BulkDeleteView):
    permission_required = "peering.delete_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    table = RoutingPolicyTable


class ProvisioningAvailableIXPeers(ObjectListView):
    permission_required = "peering.view_internetexchange"
    queryset = NetworkIXLan.objects.none()
    filterset = NetworkIXLanFilterSet
    filterset_form = NetworkIXLanFilterForm
    table = NetworkIXLanTable
    template_name = "peering/provisioning/peers.html"

    def alter_queryset(self):
        for ixp in InternetExchange.objects.all():
            self.queryset = self.queryset | ixp.get_available_peers()
