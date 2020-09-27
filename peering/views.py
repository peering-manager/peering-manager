from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.views.generic import View

from .filters import (
    AutonomousSystemFilterSet,
    BGPGroupFilterSet,
    CommunityFilterSet,
    ConfigurationFilterSet,
    DirectPeeringSessionFilterSet,
    EmailFilterSet,
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
    ConfigurationFilterForm,
    ConfigurationForm,
    DirectPeeringSessionBulkEditForm,
    DirectPeeringSessionFilterForm,
    DirectPeeringSessionForm,
    EmailFilterForm,
    EmailForm,
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
)
from .models import (
    AutonomousSystem,
    BGPGroup,
    BGPSession,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from .tables import (
    AutonomousSystemTable,
    BGPGroupTable,
    CommunityTable,
    ConfigurationTable,
    DirectPeeringSessionTable,
    EmailTable,
    InternetExchangeTable,
    InternetExchangePeeringSessionTable,
    RouterTable,
    RoutingPolicyTable,
)
from peeringdb.filters import PeerRecordFilterSet
from peeringdb.forms import PeerRecordFilterForm
from peeringdb.http import PeeringDB
from peeringdb.models import PeerRecord
from peeringdb.tables import ASPeerRecordTable, ContactTable, PeerRecordTable
from utils.views import (
    AddOrEditView,
    BulkAddFromDependencyView,
    BulkEditView,
    BulkDeleteView,
    DeleteView,
    ModelListView,
    PermissionRequiredMixin,
    TableImportView,
)


class ASList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.annotate(
        directpeeringsession_count=Count("directpeeringsession", distinct=True),
        internetexchangepeeringsession_count=Count(
            "internetexchangepeeringsession", distinct=True
        ),
    ).order_by("asn")
    filter = AutonomousSystemFilterSet
    filter_form = AutonomousSystemFilterForm
    table = AutonomousSystemTable
    template = "peering/as/list.html"


class ASAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_autonomoussystem"
    model = AutonomousSystem
    form = AutonomousSystemForm
    return_url = "peering:autonomoussystem_list"
    template = "peering/as/add_edit.html"


class ASDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_autonomoussystem"

    def get(self, request, asn):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.asn")
            )
        except AutonomousSystem.DoesNotExist:
            affiliated = None
        peeringdb_contacts = PeeringDB().get_autonomous_system_contacts(
            autonomous_system.asn
        )
        common_ix_and_sessions = []
        if affiliated:
            for ix in autonomous_system.get_common_internet_exchanges(affiliated):
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
            "peeringdb_contacts": peeringdb_contacts,
            "common_ix_and_sessions": common_ix_and_sessions,
        }
        return render(request, "peering/as/details.html", context)


class ASEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_autonomoussystem"
    model = AutonomousSystem
    form = AutonomousSystemForm
    template = "peering/as/add_edit.html"


class ASEmail(PermissionRequiredMixin, View):
    permission_required = "peering.send_email"

    def get(self, request, *args, **kwargs):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])

        if not autonomous_system.can_receive_email:
            return redirect(autonomous_system.get_absolute_url())

        form = AutonomousSystemEmailForm()
        form.fields[
            "recipient"
        ].choices = autonomous_system.get_contact_email_addresses()
        return render(
            request,
            "peering/as/email.html",
            {"autonomous_system": autonomous_system, "form": form},
        )

    def post(self, request, *args, **kwargs):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])

        if not autonomous_system.can_receive_email:
            redirect(autonomous_system.get_absolute_url())

        form = AutonomousSystemEmailForm(request.POST)
        form.fields[
            "recipient"
        ].choices = autonomous_system.get_contact_email_addresses()

        if form.is_valid():
            sent = send_mail(
                form.cleaned_data["subject"],
                form.cleaned_data["body"],
                settings.SERVER_EMAIL,
                [form.cleaned_data["recipient"]],
            )
            if sent == 1:
                messages.success(request, "Email sent.")
            else:
                messages.error(request, "Unable to send the email.")

        return redirect(autonomous_system.get_absolute_url())


class ASDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_autonomoussystem"
    model = AutonomousSystem
    return_url = "peering:autonomoussystem_list"


class ASBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_autonomoussystem"
    model = AutonomousSystem
    filter = AutonomousSystemFilterSet
    table = AutonomousSystemTable


class AutonomousSystemContacts(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_autonomoussystem"
    table = ContactTable
    template = "peering/as/contacts.html"

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of Contact objects related to the AS we
        # are looking at.
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            queryset = PeeringDB().get_autonomous_system_contacts(autonomous_system.asn)
        return queryset

    def extra_context(self, kwargs):
        extra_context = {}
        # Since we are in the context of an AS we need to keep the reference
        # for it
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            extra_context.update({"autonomous_system": autonomous_system})
        return extra_context


class AutonomousSystemDirectPeeringSessions(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_autonomoussystem"
    filter = DirectPeeringSessionFilterSet
    filter_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template = "peering/as/direct_peering_sessions.html"

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
            extra_context.update(
                {"autonomous_system": autonomous_system, "asn": autonomous_system.asn}
            )
        return extra_context


class AutonomousSystemInternetExchangesPeeringSessions(
    PermissionRequiredMixin, ModelListView
):
    permission_required = "peering.view_autonomoussystem"
    filter = InternetExchangePeeringSessionFilterSet
    filter_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template = "peering/as/internet_exchange_peering_sessions.html"
    hidden_filters = ["autonomous_system__id"]

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of InternetExchangePeeringSession objects but they
        # are linked to an AS. So first of all we need to retrieve the AS for
        # which we want to get the peering sessions.
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            queryset = (
                autonomous_system.internetexchangepeeringsession_set.prefetch_related(
                    "internet_exchange"
                ).order_by("internet_exchange", "ip_address")
            )

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}

        # Since we are in the context of an AS we need to keep the reference
        # for it
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            extra_context.update(
                {"autonomous_system": autonomous_system, "asn": autonomous_system.asn}
            )

        return extra_context


class AutonomousSystemPeers(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_autonomoussystem"
    table = ASPeerRecordTable
    template = "peering/as/peers.html"

    def build_queryset(self, request, kwargs):
        # The queryset needs to be composed of PeerRecord objects but they are linked
        # to an IX. So first of all we need to retrieve the IX on which we want to get
        # the peering sessions.
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            queryset = autonomous_system.get_available_sessions()

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}
        # Since we are in the context of an AS we need to keep the reference
        # for it
        if "asn" in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem, asn=kwargs["asn"])
            extra_context.update({"autonomous_system": autonomous_system})
        return extra_context


class AutonomousSystemAddFromPeeringDB(
    PermissionRequiredMixin, BulkAddFromDependencyView
):
    permission_required = "peering.add_internetexchangepeeringsession"
    model = InternetExchangePeeringSession
    dependency_model = PeerRecord
    form_model = InternetExchangePeeringSessionForm
    template = "peering/session/internet_exchange/add_from_peeringdb.html"

    def process_dependency_object(self, request, dependency):
        return_value = []

        for ix in InternetExchangePeeringSession.get_ix_list_for_peer_record(
            dependency
        ):
            (session6, created6) = InternetExchangePeeringSession.create_from_peeringdb(
                dependency, 6, internet_exchange=ix
            )
            (session4, created4) = InternetExchangePeeringSession.create_from_peeringdb(
                dependency, 4, internet_exchange=ix
            )

            if session6 and created6:
                return_value.append(session6)
            if session4 and created4:
                return_value.append(session4)

        return return_value

    def sort_objects(self, object_list):
        objects = []
        for object_couple in object_list:
            for obj in object_couple:
                if obj:
                    objects.append(
                        {
                            "autonomous_system": obj.autonomous_system,
                            "internet_exchange": obj.internet_exchange,
                            "ip_address": obj.ip_address,
                        }
                    )
        return objects


class BGPGroupList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_bgpgroup"
    queryset = BGPGroup.objects.annotate(
        directpeeringsession_count=Count("directpeeringsession")
    ).order_by("name", "slug")
    filter = BGPGroupFilterSet
    filter_form = BGPGroupFilterForm
    table = BGPGroupTable
    template = "peering/bgp-group/list.html"


class BGPGroupDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_bgpgroup"

    def get(self, request, slug):
        bgp_group = get_object_or_404(BGPGroup, slug=slug)
        context = {"bgpgroup": bgp_group}
        return render(request, "peering/bgp-group/details.html", context)


class BGPGroupAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_bgpgroup"
    model = BGPGroup
    form = BGPGroupForm
    return_url = "peering:bgpgroup_list"
    template = "peering/bgp-group/add_edit.html"


class BGPGroupEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_bgpgroup"
    model = BGPGroup
    form = BGPGroupForm
    template = "peering/bgp-group/add_edit.html"


class BGPGroupBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_bgpgroup"
    queryset = BGPGroup.objects.all()
    filter = BGPGroupFilterSet
    table = BGPGroupTable
    form = BGPGroupBulkEditForm


class BGPGroupDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_bgpgroup"
    model = BGPGroup
    return_url = "peering:bgpgroup_list"


class BGPGroupBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_bgpgroup"
    model = BGPGroup
    filter = BGPGroupFilterSet
    table = BGPGroupTable


class BGPGroupPeeringSessions(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_bgpgroup"
    filter = DirectPeeringSessionFilterSet
    filter_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template = "peering/bgp-group/sessions.html"
    hidden_filters = ["bgp_group"]

    def build_queryset(self, request, kwargs):
        queryset = None
        if "slug" in kwargs:
            bgp_group = get_object_or_404(BGPGroup, slug=kwargs["slug"])
            queryset = bgp_group.directpeeringsession_set.prefetch_related(
                "autonomous_system", "router"
            ).order_by("autonomous_system", "ip_address")
        return queryset

    def extra_context(self, kwargs):
        extra_context = {}
        if "slug" in kwargs:
            extra_context.update(
                {"bgpgroup": get_object_or_404(BGPGroup, slug=kwargs["slug"])}
            )
        return extra_context


class CommunityList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_community"
    queryset = Community.objects.all()
    filter = CommunityFilterSet
    filter_form = CommunityFilterForm
    table = CommunityTable
    template = "peering/community/list.html"


class CommunityAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_community"
    model = Community
    form = CommunityForm
    return_url = "peering:community_list"
    template = "peering/community/add_edit.html"


class CommunityDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_community"

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
    filter = CommunityFilterSet
    table = CommunityTable


class CommunityBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_community"
    queryset = Community.objects.all()
    filter = CommunityFilterSet
    table = CommunityTable
    form = CommunityBulkEditForm


class ConfigurationList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_configuration"
    queryset = Configuration.objects.all()
    filter = ConfigurationFilterSet
    filter_form = ConfigurationFilterForm
    table = ConfigurationTable
    template = "peering/configuration/list.html"


class ConfigurationAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_configuration"
    model = Configuration
    form = ConfigurationForm
    template = "peering/configuration/add_edit.html"
    return_url = "peering:configuration_list"


class ConfigurationDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_configuration"

    def get(self, request, pk):
        configuration = get_object_or_404(Configuration, pk=pk)
        routers = Router.objects.filter(configuration_template=configuration)
        context = {"configuration": configuration, "routers": routers}
        return render(request, "peering/configuration/details.html", context)


class ConfigurationEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_configuration"
    model = Configuration
    form = ConfigurationForm
    template = "peering/configuration/add_edit.html"


class ConfigurationDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_configuration"
    model = Configuration
    return_url = "peering:configuration_list"


class ConfigurationBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_configuration"
    model = Configuration
    filter = ConfigurationFilterSet
    table = ConfigurationTable


class DirectPeeringSessionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_directpeeringsession"
    model = DirectPeeringSession
    form = DirectPeeringSessionForm
    template = "peering/session/direct/add_edit.html"


class DirectPeeringSessionBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_directpeeringsession"
    model = DirectPeeringSession
    filter = DirectPeeringSessionFilterSet
    table = DirectPeeringSessionTable

    def filter_by_extra_context(self, queryset, request, kwargs):
        # If we are on an AutonomousSystem context, filter the session with
        # the given ASN
        if "asn" in request.POST:
            asn = request.POST.get("asn")
            autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)
            return queryset.filter(autonomous_system=autonomous_system)
        # If we are on an Router context, filter the session with
        # the given Router ID
        if "router_id" in request.POST:
            router_id = int(request.POST.get("router_id"))
            router = get_object_or_404(Router, pk=router_id)
            return queryset.filter(router=router)
        return queryset


class DirectPeeringSessionBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_directpeeringsession"
    queryset = DirectPeeringSession.objects.select_related("autonomous_system")
    parent_object = BGPSession
    filter = DirectPeeringSessionFilterSet
    table = DirectPeeringSessionTable
    form = DirectPeeringSessionBulkEditForm


class DirectPeeringSessionDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_directpeeringsession"
    model = DirectPeeringSession


class DirectPeeringSessionDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_directpeeringsession"

    def get(self, request, pk):
        peering_session = get_object_or_404(DirectPeeringSession, pk=pk)
        context = {"peering_session": peering_session}
        return render(request, "peering/session/direct/details.html", context)


class DirectPeeringSessionEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_directpeeringsession"
    model = DirectPeeringSession
    form = DirectPeeringSessionForm
    template = "peering/session/direct/add_edit.html"


class DirectPeeringSessionList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_directpeeringsession"
    queryset = DirectPeeringSession.objects.order_by("autonomous_system", "ip_address")
    table = DirectPeeringSessionTable
    filter = DirectPeeringSessionFilterSet
    filter_form = DirectPeeringSessionFilterForm
    template = "peering/session/direct/list.html"


class EmailList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_email"
    queryset = Email.objects.all()
    filter = EmailFilterSet
    filter_form = EmailFilterForm
    table = EmailTable
    template = "peering/email/list.html"


class EmailAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_email"
    model = Email
    form = EmailForm
    template = "peering/email/add_edit.html"
    return_url = "peering:email_list"


class EmailDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_email"

    def get(self, request, pk):
        context = {"email": get_object_or_404(Email, pk=pk)}
        return render(request, "peering/email/details.html", context)


class EmailEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_email"
    model = Email
    form = EmailForm
    template = "peering/email/add_edit.html"


class EmailDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_email"
    model = Email
    return_url = "peering:email_list"


class EmailBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_email"
    model = Email
    filter = EmailFilterSet
    table = EmailTable


class InternetExchangeList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_internetexchange"
    queryset = (
        InternetExchange.objects.annotate(
            internetexchangepeeringsession_count=Count("internetexchangepeeringsession")
        )
        .prefetch_related("router")
        .order_by("name", "slug")
    )
    table = InternetExchangeTable
    filter = InternetExchangeFilterSet
    filter_form = InternetExchangeFilterForm
    template = "peering/ix/list.html"


class InternetExchangeAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_internetexchange"
    model = InternetExchange
    form = InternetExchangeForm
    return_url = "peering:internetexchange_list"
    template = "peering/ix/add_edit.html"


class InternetExchangePeeringDBImport(PermissionRequiredMixin, TableImportView):
    permission_required = "peering.add_internetexchange"
    custom_formset = InternetExchangePeeringDBFormSet
    form_model = InternetExchangePeeringDBForm
    return_url = "peering:internetexchange_list"

    def get_objects(self, request):
        objects = []
        known_objects = []
        api = PeeringDB()

        for ix in InternetExchange.objects.all():
            if ix.peeringdb_id:
                known_objects.append(ix.peeringdb_id)

        ix_networks = (
            api.get_ix_networks_for_asn(request.user.preferences.get("context.asn"))
            or []
        )
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


class InternetExchangeDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_internetexchange"

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
    return_url = "peering:internetexchange_list"


class InternetExchangeBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_internetexchange"
    model = InternetExchange
    filter = InternetExchangeFilterSet
    table = InternetExchangeTable


class InternetExchangeBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_internetexchange"
    queryset = InternetExchange.objects.all()
    filter = InternetExchangeFilterSet
    table = InternetExchangeTable
    form = InternetExchangeBulkEditForm


class InternetExchangePeeringSessions(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_internetexchange"
    filter = InternetExchangePeeringSessionFilterSet
    filter_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template = "peering/ix/sessions.html"
    hidden_filters = ["internet_exchange__id"]

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of InternetExchangePeeringSession objects
        # but they are linked to an IX. So first of all we need to retrieve the IX on
        # which we want to get the peering sessions.
        if "slug" in kwargs:
            internet_exchange = get_object_or_404(InternetExchange, slug=kwargs["slug"])
            queryset = (
                internet_exchange.internetexchangepeeringsession_set.prefetch_related(
                    "autonomous_system"
                ).order_by("autonomous_system", "ip_address")
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
                    ),
                    "internet_exchange_slug": kwargs["slug"],
                }
            )

        return extra_context


class InternetExchangePeers(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_internetexchange"
    filter = PeerRecordFilterSet
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
        # Keep track of its ID as well to be able to find the IX when adding sessions
        if "slug" in kwargs:
            ix = get_object_or_404(InternetExchange, slug=kwargs["slug"])
            extra_context.update(internet_exchange=ix, internet_exchange_id=ix.pk)

        return extra_context


class InternetExchangePeeringSessionList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.order_by(
        "autonomous_system", "ip_address"
    )
    table = InternetExchangePeeringSessionTable
    filter = InternetExchangePeeringSessionFilterSet
    filter_form = InternetExchangePeeringSessionFilterForm
    template = "peering/session/internet_exchange/list.html"


class InternetExchangePeeringSessionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_internetexchangepeeringsession"
    model = InternetExchangePeeringSession
    form = InternetExchangePeeringSessionForm
    template = "peering/session/internet_exchange/add_edit.html"


class InternetExchangePeeringSessionBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_internetexchangepeeringsession"
    queryset = InternetExchangePeeringSession.objects.select_related(
        "autonomous_system"
    )
    parent_object = BGPSession
    filter = InternetExchangePeeringSessionFilterSet
    table = InternetExchangePeeringSessionTable
    form = InternetExchangePeeringSessionBulkEditForm


class InternetExchangePeeringSessionDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_internetexchangepeeringsession"

    def get(self, request, pk):
        peering_session = get_object_or_404(InternetExchangePeeringSession, pk=pk)
        context = {
            "peering_session": peering_session,
            "is_abandoned": peering_session.is_abandoned(),
        }
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


class InternetExchangePeeringSessionAddFromPeeringDB(
    PermissionRequiredMixin, BulkAddFromDependencyView
):
    permission_required = "peering.add_internetexchangepeeringsession"
    model = InternetExchangePeeringSession
    dependency_model = PeerRecord
    form_model = InternetExchangePeeringSessionForm
    template = "peering/session/internet_exchange/add_from_peeringdb.html"

    def process_dependency_object(self, request, dependency):
        ix_id = request.POST.get("internet_exchange_id", 0)
        if not ix_id:
            ix = None
        else:
            ix = InternetExchange.objects.get(pk=ix_id)
        (session6, created6) = InternetExchangePeeringSession.create_from_peeringdb(
            dependency, 6, internet_exchange=ix
        )
        (session4, created4) = InternetExchangePeeringSession.create_from_peeringdb(
            dependency, 4, internet_exchange=ix
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
    filter = InternetExchangePeeringSessionFilterSet
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
        # If we are on an AutonomousSystem context, filter the session with
        # the given ASN
        if "asn" in request.POST:
            asn = request.POST.get("asn")
            autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)
            return queryset.filter(autonomous_system=autonomous_system)
        # If we are on a Router context, filter the session with
        # the given Router ID
        if "router_id" in request.POST:
            router_id = int(request.POST.get("router_id"))
            router = get_object_or_404(Router, pk=router_id)
            return queryset.filter(internet_exchange__router=router)
        return queryset


class RouterList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_router"
    queryset = (
        Router.objects.annotate(
            internetexchangepeeringsession_count=Count(
                "internetexchange__internetexchangepeeringsession", distinct=True
            ),
            directpeeringsession_count=Count("directpeeringsession", distinct=True),
        )
        .prefetch_related("configuration_template")
        .order_by("name")
    )
    filter = RouterFilterSet
    filter_form = RouterFilterForm
    table = RouterTable
    template = "peering/router/list.html"


class RouterAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_router"
    model = Router
    form = RouterForm
    return_url = "peering:router_list"
    template = "peering/router/add_edit.html"


class RouterDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_router"

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
    filter = RouterFilterSet
    table = RouterTable
    form = RouterBulkEditForm


class RouterBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_router"
    model = Router
    filter = RouterFilterSet
    table = RouterTable


class RouterDirectPeeringSessions(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_router"
    filter = DirectPeeringSessionFilterSet
    filter_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template = "peering/router/direct_peering_sessions.html"

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of DirectPeeringSession objects
        # related to the AS we are looking at.
        if "pk" in kwargs:
            router = get_object_or_404(Router, pk=kwargs["pk"])
            queryset = router.directpeeringsession_set.order_by(
                "relationship", "ip_address"
            )
        return queryset

    def extra_context(self, kwargs):
        extra_context = {}
        # Since we are in the context of a Router we need to keep the reference
        # for it
        if "pk" in kwargs:
            router = get_object_or_404(Router, pk=kwargs["pk"])
            extra_context.update({"router": router, "router_id": router.pk})
        return extra_context


class RouterInternetExchangesPeeringSessions(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_router"
    filter = InternetExchangePeeringSessionFilterSet
    filter_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template = "peering/router/internet_exchange_peering_sessions.html"
    hidden_filters = ["router__id"]

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of InternetExchangePeeringSession objects but they
        # are linked to an AS. So first of all we need to retrieve the AS for
        # which we want to get the peering sessions.
        if "pk" in kwargs:
            queryset = InternetExchangePeeringSession.objects.filter(
                internet_exchange__router__id=kwargs["pk"]
            ).order_by("internet_exchange", "ip_address")

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}
        # Since we are in the context of a Router we need to keep the reference
        # for it
        if "pk" in kwargs:
            router = get_object_or_404(Router, pk=kwargs["pk"])
            extra_context.update({"router": router, "router_id": router.pk})

        return extra_context


class RoutingPolicyList(PermissionRequiredMixin, ModelListView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filter = RoutingPolicyFilterSet
    filter_form = RoutingPolicyFilterForm
    table = RoutingPolicyTable
    template = "peering/routing-policy/list.html"


class RoutingPolicyAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_routingpolicy"
    model = RoutingPolicy
    form = RoutingPolicyForm
    return_url = "peering:routingpolicy_list"
    template = "peering/routing-policy/add_edit.html"


class RoutingPolicyDetails(PermissionRequiredMixin, View):
    permission_required = "peering.view_routingpolicy"

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
    return_url = "peering:routingpolicy_list"


class RoutingPolicyBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_routingpolicy"
    model = RoutingPolicy
    filter = RoutingPolicyFilterSet
    table = RoutingPolicyTable


class RoutingPolicyBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peering.change_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filter = RoutingPolicyFilterSet
    table = RoutingPolicyTable
    form = RoutingPolicyBulkEditForm
