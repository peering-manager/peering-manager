from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import send_mail
from django.db.models import Count
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template.defaultfilters import slugify
from django.views.generic import View

import json

from .filters import (
    AutonomousSystemFilter,
    BGPGroupFilter,
    CommunityFilter,
    DirectPeeringSessionFilter,
    InternetExchangeFilter,
    InternetExchangePeeringSessionFilter,
    RouterFilter,
    RoutingPolicyFilter,
    TemplateFilter,
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
    InternetExchangePeeringDBForm,
    InternetExchangePeeringDBFormSet,
    InternetExchangePeeringSessionBulkEditForm,
    InternetExchangePeeringSessionFilterForm,
    InternetExchangePeeringSessionForm,
    RouterBulkEditForm,
    RouterFilterForm,
    RouterForm,
    RoutingPolicyBulkEditForm,
    RoutingPolicyFilterForm,
    RoutingPolicyForm,
    TemplateFilterForm,
    TemplateForm,
)
from .models import (
    AutonomousSystem,
    BGPGroup,
    BGPSession,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
    Template,
)
from .tables import (
    AutonomousSystemTable,
    BGPGroupTable,
    CommunityTable,
    DirectPeeringSessionTable,
    InternetExchangeTable,
    InternetExchangePeeringSessionTable,
    RouterTable,
    RoutingPolicyTable,
    TemplateTable,
)
from peeringdb.filters import PeerRecordFilter
from peeringdb.forms import PeerRecordFilterForm
from peeringdb.http import PeeringDB
from peeringdb.models import PeerRecord
from peeringdb.tables import PeerRecordTable
from utils.views import (
    AddOrEditView,
    BulkAddFromDependencyView,
    BulkEditView,
    BulkDeleteView,
    ConfirmationView,
    DeleteView,
    ModelListView,
    TableImportView,
)


class ASList(ModelListView):
    queryset = AutonomousSystem.objects.order_by("asn")
    filter = AutonomousSystemFilter
    filter_form = AutonomousSystemFilterForm
    table = AutonomousSystemTable
    template = "peering/as/list.html"


class ASAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_autonomoussystem"
    model = AutonomousSystem
    form = AutonomousSystemForm
    return_url = "peering:autonomous_system_list"
    template = "peering/as/add_edit.html"


class ASDetails(View):
    def get(self, request, asn):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)
        common_ix_and_sessions = []
        for ix in autonomous_system.get_common_internet_exchanges():
            common_ix_and_sessions.append(
                {
                    "internet_exchange": ix,
                    "has_potential_ix_peering_sessions": autonomous_system.has_potential_ix_peering_sessions(
                        ix
                    ),
                }
            )

        context = {
            "autonomous_system": autonomous_system,
            "common_ix_and_sessions": common_ix_and_sessions,
        }
        return render(request, "peering/as/details.html", context)


class ASEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_autonomoussystem"
    model = AutonomousSystem
    form = AutonomousSystemForm
    template = "peering/as/add_edit.html"


class ASEmail(PermissionRequiredMixin, View):
    permission_required = "peering.send_email_autonomoussystem"

    def get(self, request, *args, **kwargs):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
        form = AutonomousSystemEmailForm()
        return render(
            request,
            "peering/as/email.html",
            {"autonomous_system": autonomous_system, "form": form},
        )

    def post(self, request, *args, **kwargs):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
        form = AutonomousSystemEmailForm(request.POST)

        if form.is_valid():
            sent = send_mail(
                form.cleaned_data["subject"],
                form.cleaned_data["body"],
                settings.SERVER_EMAIL,
                [autonomous_system.contact_email],
            )
            if sent is 1:
                messages.success(request, "Email sent.")
            else:
                messages.error(request, "Unable to send the email.")

        return redirect(autonomous_system.get_absolute_url())


class ASDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_autonomoussystem"
    model = AutonomousSystem
    return_url = "peering:autonomous_system_list"


class ASBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_autonomoussystem"
    model = AutonomousSystem
    filter = AutonomousSystemFilter
    table = AutonomousSystemTable


class AutonomousSystemDirectPeeringSessions(ModelListView):
    filter = DirectPeeringSessionFilter
    filter_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template = "peering/as/direct_peering_sessions.html"
    hidden_columns = ["autonomous_system"]

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of DirectPeeringSession objects
        # related to the AS we are looking at.
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            queryset = autonomous_system.directpeeringsession_set.order_by(
                "relationship", "ip_address"
            )
        return queryset

    def extra_context(self, kwargs):
        extra_context = {}
        # Since we are in the context of an AS we need to keep the reference
        # for it
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            extra_context.update({"autonomous_system": autonomous_system})
        return extra_context


class AutonomousSystemInternetExchangesPeeringSessions(ModelListView):
    filter = InternetExchangePeeringSessionFilter
    filter_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template = "peering/as/internet_exchange_peering_sessions.html"
    hidden_columns = ["autonomous_system"]
    hidden_filters = ["autonomous_system__id"]

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of InternetExchangePeeringSession objects but they
        # are linked to an AS. So first of all we need to retrieve the AS for
        # which we want to get the peering sessions.
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            queryset = autonomous_system.internetexchangepeeringsession_set.order_by(
                "internet_exchange", "ip_address"
            )

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}

        # Since we are in the context of an AS we need to keep the reference
        # for it
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            extra_context.update({"autonomous_system": autonomous_system})

        return extra_context


class BGPGroupList(ModelListView):
    queryset = BGPGroup.objects.annotate(
        directpeeringsession_count=Count("directpeeringsession")
    )
    filter = BGPGroupFilter
    filter_form = BGPGroupFilterForm
    table = BGPGroupTable
    template = "peering/bgp-group/list.html"


class BGPGroupDetails(View):
    def get(self, request, slug):
        bgp_group = get_object_or_404(BGPGroup, slug=slug)
        context = {"bgp_group": bgp_group}
        return render(request, "peering/bgp-group/details.html", context)


class BGPGroupAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_bgpgroup"
    model = BGPGroup
    form = BGPGroupForm
    return_url = "peering:bgp_group_list"
    template = "peering/bgp-group/add_edit.html"


class BGPGroupEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_bgpgroup"
    model = BGPGroup
    form = BGPGroupForm
    template = "peering/bgp-group/add_edit.html"


class BGPGroupBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_bgpgroup"
    queryset = BGPGroup.objects.all()
    filter = BGPGroupFilter
    table = BGPGroupTable
    form = BGPGroupBulkEditForm


class BGPGroupDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_bgpgroup"
    model = BGPGroup
    return_url = "peering:bgp_group_list"


class BGPGroupBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_bgpgroup"
    model = BGPGroup
    filter = BGPGroupFilter
    table = BGPGroupTable


class BGPGroupPeeringSessions(ModelListView):
    filter = DirectPeeringSessionFilter
    filter_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template = "peering/bgp-group/sessions.html"
    hidden_columns = ["bgp_group"]
    hidden_filters = ["bgp_group"]

    def build_queryset(self, request, kwargs):
        queryset = None
        if "slug" in kwargs:
            bgp_group = get_object_or_404(BGPGroup, slug=kwargs["slug"])
            queryset = bgp_group.directpeeringsession_set.order_by(
                "autonomous_system", "ip_address"
            )
        return queryset

    def extra_context(self, kwargs):
        extra_context = {}
        if "slug" in kwargs:
            extra_context.update(
                {"bgp_group": get_object_or_404(BGPGroup, slug=kwargs["slug"])}
            )
        return extra_context

    def setup_table_columns(self, request, permissions, table, kwargs):
        table.columns.show("session_state")
        super().setup_table_columns(request, permissions, table, kwargs)


class BGPGroupPeeringSessionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_directpeeringsession"
    model = DirectPeeringSession
    form = DirectPeeringSessionForm
    template = "peering/session/direct/add_edit.html"

    def get_object(self, kwargs):
        if "pk" in kwargs:
            return get_object_or_404(self.model, pk=kwargs["pk"])

        return self.model()

    def alter_object(self, obj, request, args, kwargs):
        if "slug" in kwargs:
            obj.bgp_group = get_object_or_404(BGPGroup, slug=kwargs["slug"])

        return obj

    def get_return_url(self, obj):
        return obj.bgp_group.get_peering_sessions_list_url()


class CommunityList(ModelListView):
    queryset = Community.objects.all()
    filter = CommunityFilter
    filter_form = CommunityFilterForm
    table = CommunityTable
    template = "peering/community/list.html"


class CommunityAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_community"
    model = Community
    form = CommunityForm
    return_url = "peering:community_list"
    template = "peering/community/add_edit.html"


class CommunityDetails(View):
    def get(self, request, pk):
        community = get_object_or_404(Community, pk=pk)
        context = {"community": community}
        return render(request, "peering/community/details.html", context)


class CommunityEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_community"
    model = Community
    form = CommunityForm
    template = "peering/community/add_edit.html"


class CommunityDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_community"
    model = Community
    return_url = "peering:community_list"


class CommunityBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_community"
    model = Community
    filter = CommunityFilter
    table = CommunityTable


class CommunityBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_community"
    queryset = Community.objects.all()
    filter = CommunityFilter
    table = CommunityTable
    form = CommunityBulkEditForm


class DirectPeeringSessionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_directpeeringsession"
    model = DirectPeeringSession
    form = DirectPeeringSessionForm
    template = "peering/session/direct/add_edit.html"

    def get_object(self, kwargs):
        if "pk" in kwargs:
            return get_object_or_404(self.model, pk=kwargs["pk"])

        return self.model()

    def alter_object(self, obj, request, args, kwargs):
        obj.local_asn = settings.MY_ASN
        if "asn" in kwargs:
            obj.autonomous_system = get_object_or_404(
                AutonomousSystem, asn=kwargs["asn"]
            )

        return obj

    def get_return_url(self, obj):
        return obj.autonomous_system.get_direct_peering_sessions_list_url()


class DirectPeeringSessionBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_directpeeringsession"
    model = DirectPeeringSession
    filter = DirectPeeringSessionFilter
    table = DirectPeeringSessionTable


class DirectPeeringSessionBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_directpeeringsession"
    queryset = DirectPeeringSession.objects.select_related("autonomous_system")
    parent_object = BGPSession
    filter = DirectPeeringSessionFilter
    table = DirectPeeringSessionTable
    form = DirectPeeringSessionBulkEditForm


class DirectPeeringSessionDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_directpeeringsession"
    model = DirectPeeringSession

    def get_return_url(self, obj):
        return obj.autonomous_system.get_direct_peering_sessions_list_url()


class DirectPeeringSessionDetails(View):
    def get(self, request, pk):
        peering_session = get_object_or_404(DirectPeeringSession, pk=pk)
        context = {"peering_session": peering_session}
        return render(request, "peering/session/direct/details.html", context)


class DirectPeeringSessionDisable(PermissionRequiredMixin, View):
    permission_required = "peering.change_directpeeringsession"

    def get(self, request, pk):
        peering_session = get_object_or_404(DirectPeeringSession, pk=pk)
        peering_session.enabled = False
        peering_session.save()
        return redirect(peering_session.get_absolute_url())


class DirectPeeringSessionEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_directpeeringsession"
    model = DirectPeeringSession
    form = DirectPeeringSessionForm
    template = "peering/session/direct/add_edit.html"


class DirectPeeringSessionEnable(PermissionRequiredMixin, View):
    permission_required = "peering.change_directpeeringsession"

    def get(self, request, pk):
        peering_session = get_object_or_404(DirectPeeringSession, pk=pk)
        peering_session.enabled = True
        peering_session.save()
        return redirect(peering_session.get_absolute_url())


class DirectPeeringSessionList(ModelListView):
    queryset = DirectPeeringSession.objects.order_by("autonomous_system")
    table = DirectPeeringSessionTable
    filter = DirectPeeringSessionFilter
    filter_form = DirectPeeringSessionFilterForm
    template = "peering/session/direct/list.html"


class InternetExchangeList(ModelListView):
    queryset = InternetExchange.objects.order_by("name")
    table = InternetExchangeTable
    filter = InternetExchangeFilter
    filter_form = InternetExchangeFilterForm
    template = "peering/ix/list.html"


class InternetExchangeAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_internetexchange"
    model = InternetExchange
    form = InternetExchangeForm
    return_url = "peering:internet_exchange_list"
    template = "peering/ix/add_edit.html"


class InternetExchangePeeringDBImport(PermissionRequiredMixin, TableImportView):
    permission_required = "peering.add_internetexchange"
    custom_formset = InternetExchangePeeringDBFormSet
    form_model = InternetExchangePeeringDBForm
    return_url = "peering:internet_exchange_list"

    def get_objects(self):
        objects = []
        known_objects = []
        api = PeeringDB()

        for ix in InternetExchange.objects.all():
            if ix.peeringdb_id:
                known_objects.append(ix.peeringdb_id)

        ix_networks = api.get_ix_networks_for_asn(settings.MY_ASN) or []
        slugs_occurences = {}

        for ix_network in ix_networks:
            if ix_network.id not in known_objects:
                slug = slugify(ix_network.name)

                if slug in slugs_occurences:
                    slugs_occurences[slug] += 1
                    slug = "{}-{}".format(slug, slugs_occurences[slug])
                else:
                    slugs_occurences[slug] = 0

                objects.append(
                    {
                        "peeringdb_id": ix_network.id,
                        "name": ix_network.name,
                        "slug": slug,
                        "ipv6_address": ix_network.ipaddr6,
                        "ipv4_address": ix_network.ipaddr4,
                    }
                )

        return objects


class InternetExchangeDetails(View):
    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)

        # Check if the PeeringDB ID is valid
        if not internet_exchange.is_peeringdb_valid():
            # If not, try to fix it automatically
            peeringdb_id = internet_exchange.get_peeringdb_id()
            if peeringdb_id != 0:
                internet_exchange.peeringdb_id = peeringdb_id
                internet_exchange.save()
                messages.info(
                    request,
                    "The PeeringDB record reference for this IX was invalid, it has been fixed.",
                )

        context = {"internet_exchange": internet_exchange}
        return render(request, "peering/ix/details.html", context)


class InternetExchangeEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_internetexchange"
    model = InternetExchange
    form = InternetExchangeForm
    template = "peering/ix/add_edit.html"


class InternetExchangeDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_internetexchange"
    model = InternetExchange
    return_url = "peering:internet_exchange_list"


class InternetExchangeBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_internetexchange"
    model = InternetExchange
    filter = InternetExchangeFilter
    table = InternetExchangeTable


class InternetExchangeBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_internetexchange"
    queryset = InternetExchange.objects.all()
    filter = InternetExchangeFilter
    table = InternetExchangeTable
    form = InternetExchangeBulkEditForm


class InternetExchangePeeringSessions(ModelListView):
    filter = InternetExchangePeeringSessionFilter
    filter_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template = "peering/ix/sessions.html"
    hidden_columns = ["internet_exchange"]
    hidden_filters = ["internet_exchange__id"]

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of InternetExchangePeeringSession objects
        # but they are linked to an IX. So first of all we need to retrieve the IX on
        # which we want to get the peering sessions.
        if "slug" in kwargs:
            internet_exchange = get_object_or_404(InternetExchange, slug=kwargs["slug"])
            queryset = internet_exchange.internetexchangepeeringsession_set.order_by(
                "autonomous_system", "ip_address"
            )

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}

        # Since we are in the context of an IX we need to keep the reference for it
        if "slug" in kwargs:
            extra_context.update(
                {
                    "internet_exchange": get_object_or_404(
                        InternetExchange, slug=kwargs["slug"]
                    )
                }
            )

        return extra_context

    def setup_table_columns(self, request, permissions, table, kwargs):
        if "slug" in kwargs:
            internet_exchange = get_object_or_404(InternetExchange, slug=kwargs["slug"])

            if (
                internet_exchange.check_bgp_session_states
                and internet_exchange.router
                and internet_exchange.router.can_napalm_get_bgp_neighbors_detail()
            ):
                if "session_state" in table.base_columns:
                    table.columns.show("session_state")

        super().setup_table_columns(request, permissions, table, kwargs)


class InternetExchangePeers(ModelListView):
    filter = PeerRecordFilter
    filter_form = PeerRecordFilterForm
    table = PeerRecordTable
    template = "peering/ix/peers.html"

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of PeerRecord objects but they are linked
        # to an IX. So first of all we need to retrieve the IX on which we want to get
        # the peering sessions.
        if "slug" in kwargs:
            internet_exchange = get_object_or_404(InternetExchange, slug=kwargs["slug"])
            queryset = internet_exchange.get_available_peers()

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}

        # Since we are in the context of an IX we need to keep the reference for it
        if "slug" in kwargs:
            extra_context.update(
                {
                    "internet_exchange": get_object_or_404(
                        InternetExchange, slug=kwargs["slug"]
                    )
                }
            )

        return extra_context


class InternetExchangePeeringSessionList(ModelListView):
    queryset = InternetExchangePeeringSession.objects.order_by("autonomous_system")
    table = InternetExchangePeeringSessionTable
    filter = InternetExchangePeeringSessionFilter
    filter_form = InternetExchangePeeringSessionFilterForm
    template = "peering/session/internet_exchange/list.html"


class InternetExchangePeeringSessionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_internetexchangepeeringsession"
    model = InternetExchangePeeringSession
    form = InternetExchangePeeringSessionForm
    template = "peering/session/internet_exchange/add_edit.html"

    def get_object(self, kwargs):
        if "pk" in kwargs:
            return get_object_or_404(self.model, pk=kwargs["pk"])

        return self.model()

    def alter_object(self, obj, request, args, kwargs):
        if "slug" in kwargs:
            obj.internet_exchange = get_object_or_404(
                InternetExchange, slug=kwargs["slug"]
            )

        return obj

    def get_return_url(self, obj):
        return obj.internet_exchange.get_peering_sessions_list_url()


class InternetExchangePeeringSessionBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.select_related(
        "autonomous_system"
    )
    parent_object = BGPSession
    filter = InternetExchangePeeringSessionFilter
    table = InternetExchangePeeringSessionTable
    form = InternetExchangePeeringSessionBulkEditForm


class InternetExchangePeeringSessionDetails(View):
    def get(self, request, pk):
        peering_session = get_object_or_404(InternetExchangePeeringSession, pk=pk)
        context = {"peering_session": peering_session}
        return render(
            request, "peering/session/internet_exchange/details.html", context
        )


class InternetExchangePeeringSessionEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_internetexchangepeeringsession"
    model = InternetExchangePeeringSession
    form = InternetExchangePeeringSessionForm
    template = "peering/session/internet_exchange/add_edit.html"


class InternetExchangePeeringSessionDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_internetexchangepeeringsession"
    model = InternetExchangePeeringSession

    def get_return_url(self, obj):
        return obj.internet_exchange.get_peering_sessions_list_url()


class InternetExchangePeeringSessionAddFromPeeringDB(
    PermissionRequiredMixin, BulkAddFromDependencyView
):
    permission_required = "peering.add_internetexchangepeeringsession"
    model = InternetExchangePeeringSession
    dependency_model = PeerRecord
    form_model = InternetExchangePeeringSessionForm
    template = "peering/session/internet_exchange/add_from_peeringdb.html"

    def process_dependency_object(self, dependency):
        session6, created6 = InternetExchangePeeringSession.get_from_peeringdb_peer_record(
            dependency, 6
        )
        session4, created4 = InternetExchangePeeringSession.get_from_peeringdb_peer_record(
            dependency, 4
        )
        return_value = []

        if session6 and created6:
            return_value.append(session6)
        if session4 and created4:
            return_value.append(session4)

        return return_value

    def sort_objects(self, object_list):
        objects = []
        for object_couple in object_list:
            for object in object_couple:
                if object:
                    objects.append(
                        {
                            "autonomous_system": object.autonomous_system,
                            "internet_exchange": object.internet_exchange,
                            "ip_address": object.ip_address,
                        }
                    )
        return objects


class InternetExchangePeeringSessionBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_internetexchangepeeringsession"
    model = InternetExchangePeeringSession
    filter = InternetExchangePeeringSessionFilter
    table = InternetExchangePeeringSessionTable

    def filter_by_extra_context(self, queryset, request, kwargs):
        # If we are on an Internet exchange context, filter the session with
        # the given IX
        if "internet_exchange_slug" in request.POST:
            internet_exchange_slug = request.POST.get("internet_exchange_slug")
            internet_exchange = get_object_or_404(
                InternetExchange, slug=internet_exchange_slug
            )
            return queryset.filter(internet_exchange=internet_exchange)
        return queryset


class InternetExchangePeeringSessionDisable(PermissionRequiredMixin, View):
    permission_required = "peering.change_internetexchangepeeringsession"

    def get(self, request, pk):
        peering_session = get_object_or_404(InternetExchangePeeringSession, pk=pk)
        peering_session.enabled = False
        peering_session.save()
        return redirect(peering_session.get_absolute_url())


class InternetExchangePeeringSessionEnable(PermissionRequiredMixin, View):
    permission_required = "peering.change_internetexchangepeeringsession"

    def get(self, request, pk):
        peering_session = get_object_or_404(InternetExchangePeeringSession, pk=pk)
        peering_session.enabled = True
        peering_session.save()
        return redirect(peering_session.get_absolute_url())


class RouterList(ModelListView):
    queryset = Router.objects.all()
    filter = RouterFilter
    filter_form = RouterFilterForm
    table = RouterTable
    template = "peering/router/list.html"


class RouterAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_router"
    model = Router
    form = RouterForm
    return_url = "peering:router_list"
    template = "peering/router/add_edit.html"


class RouterDetails(View):
    def get(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        internet_exchanges = InternetExchange.objects.filter(router=router)
        context = {"router": router, "internet_exchanges": internet_exchanges}
        return render(request, "peering/router/details.html", context)


class RouterConfiguration(PermissionRequiredMixin, View):
    permission_required = "peering.view_configuration_router"

    def get(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        context = {
            "router": router,
            "router_configuration": router.generate_configuration(),
        }

        # Asked for raw output
        if "raw" in request.GET:
            return HttpResponse(
                context["router_configuration"], content_type="text/plain"
            )
        return render(request, "peering/router/configuration.html", context)


class RouterEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_router"
    model = Router
    form = RouterForm
    template = "peering/router/add_edit.html"


class RouterDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_router"
    model = Router
    return_url = "peering:router_list"


class RouterBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_router"
    queryset = Router.objects.all()
    filter = RouterFilter
    table = RouterTable
    form = RouterBulkEditForm


class RouterBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_router"
    model = Router
    filter = RouterFilter
    table = RouterTable


class RoutingPolicyList(ModelListView):
    queryset = RoutingPolicy.objects.all()
    filter = RoutingPolicyFilter
    filter_form = RoutingPolicyFilterForm
    table = RoutingPolicyTable
    template = "peering/routing-policy/list.html"


class RoutingPolicyAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_routingpolicy"
    model = RoutingPolicy
    form = RoutingPolicyForm
    return_url = "peering:routing_policy_list"
    template = "peering/routing-policy/add_edit.html"


class RoutingPolicyDetails(View):
    def get(self, request, pk):
        routing_policy = get_object_or_404(RoutingPolicy, pk=pk)
        context = {"routing_policy": routing_policy}
        return render(request, "peering/routing-policy/details.html", context)


class RoutingPolicyEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_routingpolicy"
    model = RoutingPolicy
    form = RoutingPolicyForm
    template = "peering/routing-policy/add_edit.html"


class RoutingPolicyDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_routingpolicy"
    model = RoutingPolicy
    return_url = "peering:routing_policy_list"


class RoutingPolicyBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_routingpolicy"
    model = RoutingPolicy
    filter = RoutingPolicyFilter
    table = RoutingPolicyTable


class RoutingPolicyBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filter = RoutingPolicyFilter
    table = RoutingPolicyTable
    form = RoutingPolicyBulkEditForm


class TemplateList(ModelListView):
    queryset = Template.objects.all()
    filter = TemplateFilter
    filter_form = TemplateFilterForm
    table = TemplateTable
    template = "peering/template/list.html"


class TemplateAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_template"
    model = Template
    form = TemplateForm
    template = "peering/template/add_edit.html"
    return_url = "peering:template_list"


class TemplateDetails(View):
    def get(self, request, pk):
        template = get_object_or_404(Template, pk=pk)
        routers = Router.objects.filter(configuration_template=template)
        context = {"template": template, "routers": routers}
        return render(request, "peering/template/details.html", context)


class TemplateEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_template"
    model = Template
    form = TemplateForm
    template = "peering/template/add_edit.html"


class TemplateDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_template"
    model = Template
    return_url = "peering:template_list"


class TemplateBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_template"
    model = Template
    filter = TemplateFilter
    table = TemplateTable
