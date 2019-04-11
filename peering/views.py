from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template.defaultfilters import slugify
from django.views.generic import View

import json

from .filters import (
    AutonomousSystemFilter,
    CommunityFilter,
    ConfigurationTemplateFilter,
    DirectPeeringSessionFilter,
    InternetExchangeFilter,
    PeerRecordFilter,
    InternetExchangePeeringSessionFilter,
    RouterFilter,
    RoutingPolicyFilter,
)
from .forms import (
    AutonomousSystemForm,
    AutonomousSystemFilterForm,
    CommunityForm,
    CommunityFilterForm,
    CommunityBulkEditForm,
    ConfigurationTemplateForm,
    ConfigurationTemplateFilterForm,
    DirectPeeringSessionBulkEditForm,
    DirectPeeringSessionForm,
    DirectPeeringSessionFilterForm,
    DirectPeeringSessionRoutingPolicyForm,
    InternetExchangeForm,
    InternetExchangeBulkEditForm,
    InternetExchangePeeringDBForm,
    InternetExchangePeeringDBFormSet,
    InternetExchangeCommunityForm,
    InternetExchangeRoutingPolicyForm,
    InternetExchangeFilterForm,
    PeerRecordFilterForm,
    InternetExchangePeeringSessionBulkEditForm,
    InternetExchangePeeringSessionForm,
    InternetExchangePeeringSessionFilterForm,
    InternetExchangePeeringSessionFilterFormForIX,
    InternetExchangePeeringSessionFilterFormForAS,
    InternetExchangePeeringSessionRoutingPolicyForm,
    RouterForm,
    RouterFilterForm,
    RouterBulkEditForm,
    RoutingPolicyForm,
    RoutingPolicyBulkEditForm,
    RoutingPolicyFilterForm,
)
from .models import (
    AutonomousSystem,
    BGPSession,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from .tables import (
    AutonomousSystemTable,
    CommunityTable,
    ConfigurationTemplateTable,
    DirectPeeringSessionTable,
    InternetExchangeTable,
    PeerRecordTable,
    InternetExchangePeeringSessionTable,
    RouterTable,
    RoutingPolicyTable,
)
from peeringdb.http import PeeringDB
from peeringdb.models import PeerRecord
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
    filter_form = InternetExchangePeeringSessionFilterFormForAS
    table = InternetExchangePeeringSessionTable
    template = "peering/as/internet_exchange_peering_sessions.html"
    hidden_columns = ["asn", "autonomous_system"]

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


class ConfigTemplateList(ModelListView):
    queryset = ConfigurationTemplate.objects.all()
    filter = ConfigurationTemplateFilter
    filter_form = ConfigurationTemplateFilterForm
    table = ConfigurationTemplateTable
    template = "peering/config/list.html"


class ConfigTemplateAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.add_configurationtemplate"
    model = ConfigurationTemplate
    form = ConfigurationTemplateForm
    return_url = "peering:configuration_template_list"


class ConfigTemplateDetails(View):
    def get(self, request, pk):
        configuration_template = get_object_or_404(ConfigurationTemplate, pk=pk)
        internet_exchanges = InternetExchange.objects.filter(
            configuration_template=configuration_template
        )
        context = {
            "configuration_template": configuration_template,
            "internet_exchanges": internet_exchanges,
        }
        return render(request, "peering/config/details.html", context)


class ConfigTemplateEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_configurationtemplate"
    model = ConfigurationTemplate
    form = ConfigurationTemplateForm


class ConfigTemplateDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "peering.delete_configurationtemplate"
    model = ConfigurationTemplate
    return_url = "peering:configuration_template_list"


class ConfigTemplateBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "peering.delete_configurationtemplate"
    model = ConfigurationTemplate
    filter = ConfigurationTemplateFilter
    table = ConfigurationTemplateTable


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


class DirectPeeringSessionUpdateRoutingPolicies(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_directpeeringsession"
    model = DirectPeeringSession
    form = DirectPeeringSessionRoutingPolicyForm
    template = "peering/session/routing_policies.html"

    def get(self, request, *args, **kwargs):
        obj = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        form = self.form(instance=obj)

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object(kwargs)
        form = self.form(request.POST, instance=obj)

        if form.is_valid():
            # Clear routing policies to avoid duplicates
            obj.export_routing_policies.clear()
            obj.import_routing_policies.clear()

            # Add routing policies one by one
            for routing_policy in request.POST.getlist("export_routing_policies"):
                obj.export_routing_policies.add(routing_policy)
            for routing_policy in request.POST.getlist("import_routing_policies"):
                obj.import_routing_policies.add(routing_policy)
            # Save the object and its linked communities
            obj.save()

            return redirect(self.get_return_url(obj))

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )


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
        for ix_network in ix_networks:
            if ix_network.id not in known_objects:
                objects.append(
                    {
                        "peeringdb_id": ix_network.id,
                        "name": ix_network.name,
                        "slug": slugify(ix_network.name),
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


class InternetExchangeUpdateCommunities(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_internetexchange"
    model = InternetExchange
    form = InternetExchangeCommunityForm
    template = "peering/ix/communities.html"

    def get(self, request, *args, **kwargs):
        obj = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        form = self.form(instance=obj)

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object(kwargs)
        form = self.form(request.POST, instance=obj)

        if form.is_valid():
            # Clear communities to avoid duplicates
            obj.communities.clear()
            # Add communities one by one
            for community in request.POST.getlist("communities"):
                obj.communities.add(community)
            # Save the object and its linked communities
            obj.save()

            return redirect(self.get_return_url(obj))

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )


class InternetExchangeUpdateRoutingPolicies(PermissionRequiredMixin, AddOrEditView):
    permission_required = "peering.change_internetexchange"
    model = InternetExchange
    form = InternetExchangeRoutingPolicyForm
    template = "peering/ix/routing_policies.html"

    def get(self, request, *args, **kwargs):
        obj = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        form = self.form(instance=obj)

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object(kwargs)
        form = self.form(request.POST, instance=obj)

        if form.is_valid():
            # Clear routing policies to avoid duplicates
            obj.export_routing_policies.clear()
            obj.import_routing_policies.clear()

            # Add routing policies one by one
            for routing_policy in request.POST.getlist("export_routing_policies"):
                obj.export_routing_policies.add(routing_policy)
            for routing_policy in request.POST.getlist("import_routing_policies"):
                obj.import_routing_policies.add(routing_policy)
            # Save the object and its linked communities
            obj.save()

            return redirect(self.get_return_url(obj))

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )


class InternetExchangePeeringSessions(ModelListView):
    filter = InternetExchangePeeringSessionFilter
    filter_form = InternetExchangePeeringSessionFilterFormForIX
    table = InternetExchangePeeringSessionTable
    template = "peering/ix/sessions.html"
    hidden_columns = ["internet_exchange"]

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of InternetExchangePeeringSession objects
        # but they are linked to an IX. So first of all we need to retrieve the IX on
        # which we want to get the peering sessions.
        if "slug" in kwargs:
            internet_exchange = get_object_or_404(InternetExchange, slug=kwargs["slug"])
            queryset = internet_exchange.internetexchangepeeringsession_set.order_by(
                "autonomous_system.asn", "ip_address"
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


class InternetExchangeConfig(PermissionRequiredMixin, View):
    permission_required = "peering.view_configuration_internetexchange"

    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)

        context = {
            "internet_exchange": internet_exchange,
            "internet_exchange_configuration": internet_exchange.generate_configuration(),
        }

        return render(request, "peering/ix/configuration.html", context)


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


class InternetExchangePeeringSessionUpdateRoutingPolicies(
    PermissionRequiredMixin, AddOrEditView
):
    permission_required = "peering.change_internetexchangepeeringsession"
    model = InternetExchangePeeringSession
    form = InternetExchangePeeringSessionRoutingPolicyForm
    template = "peering/session/routing_policies.html"

    def get(self, request, *args, **kwargs):
        obj = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        form = self.form(instance=obj)

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object(kwargs)
        form = self.form(request.POST, instance=obj)

        if form.is_valid():
            # Clear routing policies to avoid duplicates
            obj.export_routing_policies.clear()
            obj.import_routing_policies.clear()

            # Add routing policies one by one
            for routing_policy in request.POST.getlist("export_routing_policies"):
                obj.export_routing_policies.add(routing_policy)
            for routing_policy in request.POST.getlist("import_routing_policies"):
                obj.import_routing_policies.add(routing_policy)
            # Save the object and its linked communities
            obj.save()

            return redirect(self.get_return_url(obj))

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )


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
