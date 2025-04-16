from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.views.generic import View

from extras.constants import EMAIL_SENT_JOURNAL_TEMPLATE
from extras.enums import JournalEntryKind
from extras.models import JournalEntry
from extras.views import ObjectConfigContextView
from net.filtersets import ConnectionFilterSet
from net.forms import ConnectionFilterForm
from net.models import Connection
from net.tables import ConnectionTable
from peering_manager.views.generic import (
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
from peeringdb.filtersets import NetworkIXLanFilterSet
from peeringdb.forms import NetworkIXLanFilterForm
from peeringdb.tables import NetworkIXLanTable
from utils.forms import ConfirmationForm
from utils.functions import count_related

from .filtersets import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    CommunityFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangeFilterSet,
    InternetExchangePeeringSessionFilterSet,
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
    NetworkIXLan,
    RoutingPolicy,
)
from .tables import (
    AutonomousSystemTable,
    BGPGroupTable,
    CommunityTable,
    DirectPeeringSessionTable,
    InternetExchangePeeringSessionTable,
    InternetExchangeTable,
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
    tab = "main"

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

        return {"shared_internet_exchanges": shared_internet_exchanges}


class AutonomousSystemConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    base_template = "peering/autonomoussystem/_base.html"


class AutonomousSystemEdit(ObjectEditView):
    queryset = AutonomousSystem.objects.defer("prefixes")
    form = AutonomousSystemForm
    template_name = "peering/autonomoussystem/edit.html"


class AutonomousSystemDelete(ObjectDeleteView):
    permission_required = "peering.delete_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")


class AutonomousSystemBulkDelete(BulkDeleteView):
    queryset = AutonomousSystem.objects.defer("prefixes")
    filterset = AutonomousSystemFilterSet
    table = AutonomousSystemTable


class AutonomousSystemPeeringDB(ObjectView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    template_name = "peering/autonomoussystem/peeringdb.html"
    tab = "peeringdb"

    def get_extra_context(self, request, instance):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
            facilities = instance.get_peeringdb_shared_facilities(affiliated)
        except AutonomousSystem.DoesNotExist:
            facilities = []

        return {"contacts": instance.peeringdb_contacts, "facilities": facilities}


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
    tab = "direct-sessions"

    def get_children(self, request, parent):
        return (
            parent.get_direct_peering_sessions()
            .prefetch_related("bgp_group")
            .order_by("bgp_group", "relationship", "ip_address")
        )


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
    tab = "ixp-sessions"

    def get_children(self, request, parent):
        return (
            parent.get_ixp_peering_sessions()
            .prefetch_related("ixp_connection")
            .order_by("ixp_connection", "ip_address")
        )


class AutonomousSystemPeers(ObjectChildrenView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    child_model = NetworkIXLan
    table = NetworkIXLanTable
    template_name = "peering/autonomoussystem/peers.html"
    tab = "peers"

    def get_children(self, request, parent):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            affiliated = None

        return parent.get_missing_peering_sessions(affiliated)


class AutonomousSystemEmail(PermissionRequiredMixin, View):
    permission_required = "peering.send_email"
    tab = "email"

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
            {"instance": instance, "form": form, "tab": self.tab},
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

            try:
                sent = mail.send()
                error_message = None
            except Exception as exc:
                sent = 0
                error_message = f"Unable to send e-mail: {exc!s}"

            if error_message:
                message = mark_safe(
                    "Unable to send the e-mail, see "
                    f'<a href="{reverse("peering:autonomoussystem_journal", kwargs={"pk": instance.pk})}">'
                    "journal</a> for more details."
                )
                messages.error(request, message)
            elif not sent:
                message = "E-mail not sent, no recipients."
                messages.warning(request, message)
            else:
                message = "E-mail sent."
                messages.success(request, message)

            JournalEntry.log(
                object=instance,
                comments=EMAIL_SENT_JOURNAL_TEMPLATE.format(
                    message=error_message or message,
                    recipients=", ".join(mail.to),
                    cc=", ".join(mail.cc),
                    sender=mail.from_email,
                    subject=mail.subject,
                    body=mail.body,
                ),
                user=request.user,
                kind=(
                    JournalEntryKind.DANGER if error_message else JournalEntryKind.INFO
                ),
            )

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
    tab = "main"


class BGPGroupConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_bgpgroup"
    queryset = BGPGroup.objects.all()
    base_template = "peering/bgpgroup/_base.html"


class BGPGroupEdit(ObjectEditView):
    queryset = BGPGroup.objects.all()
    form = BGPGroupForm


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
    tab = "direct-sessions"

    def get_children(self, request, parent):
        return parent.directpeeringsession_set.prefetch_related(
            "autonomous_system", "router"
        ).order_by("autonomous_system", "ip_address")


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
    tab = "main"


class CommunityConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_community"
    queryset = Community.objects.all()
    base_template = "peering/community/_base.html"


class CommunityEdit(ObjectEditView):
    queryset = Community.objects.all()
    form = CommunityForm


class CommunityDelete(ObjectDeleteView):
    permission_required = "peering.delete_community"
    queryset = Community.objects.all()


class CommunityBulkDelete(BulkDeleteView):
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
    tab = "main"


class DirectPeeringSessionConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_directpeeringsession"
    queryset = DirectPeeringSession.objects.all()
    base_template = "peering/directpeeringsession/_base.html"


class DirectPeeringSessionEdit(ObjectEditView):
    queryset = DirectPeeringSession.objects.all()
    form = DirectPeeringSessionForm


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
    tab = "main"

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


class InternetExchangeConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_internetexchange"
    queryset = InternetExchange.objects.all()
    base_template = "peering/internetexchange/_base.html"


class InternetExchangeEdit(ObjectEditView):
    queryset = InternetExchange.objects.all()
    form = InternetExchangeForm


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
    tab = "connections"

    def get_children(self, request, parent):
        return Connection.objects.filter(internet_exchange_point=parent)


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
    tab = "sessions"

    def get_children(self, request, parent):
        return parent.get_peering_sessions()


class InternetExchangePeers(ObjectChildrenView):
    permission_required = "peering.view_internetexchange"
    queryset = InternetExchange.objects.all()
    child_model = NetworkIXLan
    filterset = NetworkIXLanFilterSet
    filterset_form = NetworkIXLanFilterForm
    table = NetworkIXLanTable
    template_name = "peering/internetexchange/peers.html"
    tab = "peers"

    def get_children(self, request, parent):
        return parent.get_available_peers()

    def get_extra_context(self, request, instance):
        return {"internet_exchange_id": instance.pk}


class InternetExchangeIXAPI(PermissionRequiredMixin, View):
    permission_required = "peering.view_internet_exchange_point_ixapi"
    tab = "ixapi"

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
    tab = "main"


class InternetExchangePeeringSessionConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.all()
    base_template = "peering/internetexchangepeeringsession/_base.html"


class InternetExchangePeeringSessionEdit(ObjectEditView):
    queryset = InternetExchangePeeringSession.objects.all()
    form = InternetExchangePeeringSessionForm


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
    tab = "main"


class RoutingPolicyContext(ObjectConfigContextView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    base_template = "peering/routingpolicy/_base.html"


class RoutingPolicyEdit(ObjectEditView):
    queryset = RoutingPolicy.objects.all()
    form = RoutingPolicyForm


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
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    table = RoutingPolicyTable
