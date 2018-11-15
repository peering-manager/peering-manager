from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template.defaultfilters import slugify
from django.views.generic import View

import json

from .filters import (
    AutonomousSystemFilter, CommunityFilter, ConfigurationTemplateFilter,
    DirectPeeringSessionFilter, InternetExchangeFilter, PeerRecordFilter,
    InternetExchangePeeringSessionFilter, RouterFilter, RoutingPolicyFilter)
from .forms import (
    AutonomousSystemForm, AutonomousSystemCSVForm, AutonomousSystemFilterForm,
    AutonomousSystemImportFromPeeringDBForm, CommunityForm, CommunityCSVForm,
    CommunityFilterForm, ConfigurationTemplateForm,
    ConfigurationTemplateFilterForm, DirectPeeringSessionBulkEditForm,
    DirectPeeringSessionForm, DirectPeeringSessionFilterForm,
    InternetExchangeForm, InternetExchangePeeringDBForm,
    InternetExchangePeeringDBFormSet, InternetExchangeCommunityForm,
    InternetExchangeCSVForm, InternetExchangeFilterForm, PeerRecordFilterForm,
    InternetExchangePeeringSessionBulkEditForm,
    InternetExchangePeeringSessionForm,
    InternetExchangePeeringSessionFilterForm,
    InternetExchangePeeringSessionFilterFormForIX,
    InternetExchangePeeringSessionFilterFormForAS, RouterForm, RouterCSVForm,
    RouterFilterForm, RoutingPolicyCSVForm, RoutingPolicyForm,
    RoutingPolicyBulkEditForm, RoutingPolicyFilterForm)
from .models import (
    AutonomousSystem, BGPSession, Community, ConfigurationTemplate,
    DirectPeeringSession, InternetExchange, InternetExchangePeeringSession,
    Router, RoutingPolicy)
from .tables import (
    AutonomousSystemTable, CommunityTable, ConfigurationTemplateTable,
    DirectPeeringSessionTable, InternetExchangeTable, PeerRecordTable,
    InternetExchangePeeringSessionTable,
    InternetExchangePeeringSessionTableForIX,
    InternetExchangePeeringSessionTableForAS, RouterTable, RoutingPolicyTable)
from peeringdb.api import PeeringDB
from peeringdb.models import PeerRecord
from utils.models import UserAction
from utils.views import (
    AddOrEditView, BulkAddFromDependencyView, BulkEditView, BulkDeleteView,
    ConfirmationView, DeleteView, GenericFormView, ImportView, ModelListView,
    TableImportView)


class ASList(ModelListView):
    queryset = AutonomousSystem.objects.order_by('asn')
    filter = AutonomousSystemFilter
    filter_form = AutonomousSystemFilterForm
    table = AutonomousSystemTable
    template = 'peering/as/list.html'


class ASAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.add_autonomoussystem'
    model = AutonomousSystem
    form = AutonomousSystemForm
    return_url = 'peering:autonomous_system_list'
    template = 'peering/as/add_edit.html'


class ASImport(PermissionRequiredMixin, ImportView):
    permission_required = 'peering.add_autonomoussystem'
    form_model = AutonomousSystemCSVForm
    return_url = 'peering:autonomous_system_list'


class ASImportFromPeeringDB(PermissionRequiredMixin, GenericFormView):
    permission_required = 'peering.add_autonomoussystem'
    form = AutonomousSystemImportFromPeeringDBForm
    template = 'peering/as/import_from_peeringdb.html'
    return_url = 'peering:autonomous_system_list'

    def process_form(self, request, form):
        # Get form data
        asn = form.cleaned_data['asn']
        comment = form.cleaned_data['comment']

        # Try to import the AS using its PeeringDB record
        autonomous_system = AutonomousSystem.create_from_peeringdb(asn)
        # AS is valid and created
        if autonomous_system:
            if comment:
                # Add the user comment if it was submitted
                AutonomousSystem.objects.filter(
                    asn=autonomous_system.asn).update(comment=comment)

            messages.success(request, 'AS{} has been successfully '
                             'imported from PeeringDB.'.format(asn))
            return redirect(autonomous_system.get_absolute_url())

        # Not a valid AS, reject the user
        messages.error(request, 'AS{} is not valid or does not have a '
                       'valid PeeringDB record.'.format(asn))
        context = {
            'form': form,
            'return_url': reverse(self.return_url),
        }
        return render(request, self.template, context)


class ASDetails(View):
    def get(self, request, asn):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)
        common_ix_and_sessions = []

        for ix in autonomous_system.get_common_internet_exchanges():
            common_ix_and_sessions.append({
                'internet_exchange': ix,
                'sessions': autonomous_system.get_missing_peering_sessions(ix),
            })

        context = {
            'autonomous_system': autonomous_system,
            'common_ix_and_sessions': common_ix_and_sessions,
        }
        return render(request, 'peering/as/details.html', context)


class ASEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_autonomoussystem'
    model = AutonomousSystem
    form = AutonomousSystemForm
    template = 'peering/as/add_edit.html'


class ASDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'peering.delete_autonomoussystem'
    model = AutonomousSystem
    return_url = 'peering:autonomous_system_list'


class ASBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'peering.delete_autonomoussystem'
    model = AutonomousSystem
    filter = AutonomousSystemFilter
    table = AutonomousSystemTable


class ASPeeringDBSync(PermissionRequiredMixin, View):
    permission_required = 'peering.change_autonomoussystem'

    def get(self, request, asn):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)
        synced = autonomous_system.sync_with_peeringdb()

        if not synced:
            messages.error(
                request, 'Unable to synchronize AS details with PeeringDB.')
        else:
            messages.success(
                request, 'AS details have been synchronized with PeeringDB.')

        return redirect(autonomous_system.get_absolute_url())


class AutonomousSystemDirectPeeringSessions(ModelListView):
    filter = DirectPeeringSessionFilter
    filter_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template = 'peering/as/direct_peering_sessions.html'

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of DirectPeeringSession objects
        # related to the AS we are looking at.
        if 'asn' in kwargs:
            autonomous_system = get_object_or_404(AutonomousSystem,
                                                  asn=kwargs['asn'])
            queryset = autonomous_system.directpeeringsession_set.order_by(
                'relationship', 'ip_address')
        return queryset

    def extra_context(self, kwargs):
        extra_context = {}
        # Since we are in the context of an AS we need to keep the reference
        # for it
        if 'asn' in kwargs:
            autonomous_system = get_object_or_404(
                AutonomousSystem, asn=kwargs['asn'])
            extra_context.update({'autonomous_system': autonomous_system})
        return extra_context


class AutonomousSystemInternetExchangesPeeringSessions(ModelListView):
    filter = InternetExchangePeeringSessionFilter
    filter_form = InternetExchangePeeringSessionFilterFormForAS
    table = InternetExchangePeeringSessionTableForAS
    template = 'peering/as/internet_exchange_peering_sessions.html'

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of InternetExchangePeeringSession objects but they
        # are linked to an AS. So first of all we need to retrieve the AS for
        # which we want to get the peering sessions.
        if 'asn' in kwargs:
            autonomous_system = get_object_or_404(
                AutonomousSystem, asn=kwargs['asn'])
            queryset = autonomous_system.internetexchangepeeringsession_set.order_by(
                'internet_exchange', 'ip_address')

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}

        # Since we are in the context of an AS we need to keep the reference
        # for it
        if 'asn' in kwargs:
            autonomous_system = get_object_or_404(
                AutonomousSystem, asn=kwargs['asn'])
            extra_context.update({'autonomous_system': autonomous_system})

        return extra_context


class CommunityList(ModelListView):
    queryset = Community.objects.all()
    filter = CommunityFilter
    filter_form = CommunityFilterForm
    table = CommunityTable
    template = 'peering/community/list.html'


class CommunityAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.add_community'
    model = Community
    form = CommunityForm
    return_url = 'peering:community_list'
    template = 'peering/community/add_edit.html'


class CommunityImport(PermissionRequiredMixin, ImportView):
    permission_required = 'peering.add_community'
    form_model = CommunityCSVForm
    return_url = 'peering:community_list'


class CommunityDetails(View):
    def get(self, request, pk):
        community = get_object_or_404(Community, pk=pk)
        context = {
            'community': community,
        }
        return render(request, 'peering/community/details.html', context)


class CommunityEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_community'
    model = Community
    form = CommunityForm
    template = 'peering/community/add_edit.html'


class CommunityDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'peering.delete_community'
    model = Community
    return_url = 'peering:community_list'


class CommunityBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'peering.delete_community'
    model = Community
    filter = CommunityFilter
    table = CommunityTable


class ConfigTemplateList(ModelListView):
    queryset = ConfigurationTemplate.objects.all()
    filter = ConfigurationTemplateFilter
    filter_form = ConfigurationTemplateFilterForm
    table = ConfigurationTemplateTable
    template = 'peering/config/list.html'


class ConfigTemplateAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.add_configurationtemplate'
    model = ConfigurationTemplate
    form = ConfigurationTemplateForm
    return_url = 'peering:configuration_template_list'


class ConfigTemplateDetails(View):
    def get(self, request, pk):
        configuration_template = get_object_or_404(
            ConfigurationTemplate, pk=pk)
        internet_exchanges = InternetExchange.objects.filter(
            configuration_template=configuration_template)
        context = {
            'configuration_template': configuration_template,
            'internet_exchanges': internet_exchanges,
        }
        return render(request, 'peering/config/details.html', context)


class ConfigTemplateEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_configurationtemplate'
    model = ConfigurationTemplate
    form = ConfigurationTemplateForm


class ConfigTemplateDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'peering.delete_configurationtemplate'
    model = ConfigurationTemplate
    return_url = 'peering:configuration_template_list'


class ConfigTemplateBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'peering.delete_configurationtemplate'
    model = ConfigurationTemplate
    filter = ConfigurationTemplateFilter
    table = ConfigurationTemplateTable


class DirectPeeringSessionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.add_directpeeringsession'
    model = DirectPeeringSession
    form = DirectPeeringSessionForm
    template = 'peering/session/direct/add_edit.html'

    def get_object(self, kwargs):
        if 'pk' in kwargs:
            return get_object_or_404(self.model, pk=kwargs['pk'])

        return self.model()

    def alter_object(self, obj, request, args, kwargs):
        obj.local_asn = settings.MY_ASN
        if 'asn' in kwargs:
            obj.autonomous_system = get_object_or_404(AutonomousSystem,
                                                      asn=kwargs['asn'])

        return obj

    def get_return_url(self, obj):
        return obj.autonomous_system.get_direct_peering_sessions_list_url()


class DirectPeeringSessionBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'peering.delete_directpeeringsession'
    model = DirectPeeringSession
    filter = DirectPeeringSessionFilter
    table = DirectPeeringSessionTable


class DirectPeeringSessionBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = 'peering.change_directpeeringsession'
    queryset = DirectPeeringSession.objects.select_related('autonomous_system')
    parent_object = BGPSession
    filter = DirectPeeringSessionFilter
    table = DirectPeeringSessionTable
    form = DirectPeeringSessionBulkEditForm


class DirectPeeringSessionDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'peering.delete_directpeeringsession'
    model = DirectPeeringSession

    def get_return_url(self, obj):
        return obj.autonomous_system.get_direct_peering_sessions_list_url()


class DirectPeeringSessionDetails(View):
    def get(self, request, pk):
        peering_session = get_object_or_404(DirectPeeringSession, pk=pk)
        context = {'peering_session': peering_session}
        return render(request, 'peering/session/direct/details.html', context)


class DirectPeeringSessionDisable(PermissionRequiredMixin, View):
    permission_required = 'peering.change_directpeeringsession'

    def get(self, request, pk):
        peering_session = get_object_or_404(DirectPeeringSession, pk=pk)
        peering_session.enabled = False
        peering_session.save()
        return redirect(peering_session.get_absolute_url())


class DirectPeeringSessionEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_directpeeringsession'
    model = DirectPeeringSession
    form = DirectPeeringSessionForm
    template = 'peering/session/direct/add_edit.html'


class DirectPeeringSessionEnable(PermissionRequiredMixin, View):
    permission_required = 'peering.change_directpeeringsession'

    def get(self, request, pk):
        peering_session = get_object_or_404(DirectPeeringSession, pk=pk)
        peering_session.enabled = True
        peering_session.save()
        return redirect(peering_session.get_absolute_url())


class IXList(ModelListView):
    queryset = InternetExchange.objects.order_by('name')
    table = InternetExchangeTable
    filter = InternetExchangeFilter
    filter_form = InternetExchangeFilterForm
    template = 'peering/ix/list.html'


class IXAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.add_internetexchange'
    model = InternetExchange
    form = InternetExchangeForm
    return_url = 'peering:internet_exchange_list'
    template = 'peering/ix/add_edit.html'


class IXImport(PermissionRequiredMixin, ImportView):
    permission_required = 'peering.add_internetexchange'
    form_model = InternetExchangeCSVForm
    return_url = 'peering:internet_exchange_list'


class IXImportFromRouter(PermissionRequiredMixin, ConfirmationView):
    permission_required = 'peering.add_internetexchangepeeringsession'
    template = 'peering/ix/import_from_router.html'

    def extra_context(self, kwargs):
        context = {}

        if 'slug' in kwargs:
            internet_exchange = get_object_or_404(
                InternetExchange, slug=kwargs['slug'])
            context.update({'internet_exchange': internet_exchange})

        return context

    def process(self, request, kwargs):
        internet_exchange = get_object_or_404(
            InternetExchange, slug=kwargs['slug'])
        result = internet_exchange.import_peering_sessions_from_router()

        # Set the return URL
        self.return_url = internet_exchange.get_peering_sessions_list_url()

        if not result:
            messages.error(
                request, 'Cannot import peering sessions from the router.')
        else:
            if result[0] == 0 and result[1] == 0:
                messages.warning(
                    request, 'No peering sessions have been imported.')
            else:
                if result[0] > 0:
                    message = 'Imported {} {}'.format(
                        result[0], AutonomousSystem._meta.verbose_name_plural)
                    messages.success(request, message)
                    UserAction.objects.log_import(
                        request.user, AutonomousSystem, message)

                if result[1] > 0:
                    message = 'Imported {} {}'.format(
                        result[1], InternetExchangePeeringSession._meta.verbose_name_plural)
                    messages.success(request, message)
                    UserAction.objects.log_import(
                        request.user, InternetExchangePeeringSession, message)

                if result[2]:
                    message = 'Peering sessions for the following ASNs have been ignored due to missing PeeringDB entries: {}.'.format(
                        ', '.join(result[2]))
                    messages.warning(request, message)

        return redirect(self.return_url)


class IXPeeringDBImport(PermissionRequiredMixin, TableImportView):
    permission_required = 'peering.add_internetexchange'
    custom_formset = InternetExchangePeeringDBFormSet
    form_model = InternetExchangePeeringDBForm
    return_url = 'peering:internet_exchange_list'

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
                objects.append({
                    'peeringdb_id': ix_network.id,
                    'name': ix_network.name,
                    'slug': slugify(ix_network.name),
                    'ipv6_address': ix_network.ipaddr6,
                    'ipv4_address': ix_network.ipaddr4,
                })

        return objects


class IXDetails(View):
    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)
        context = {
            'internet_exchange': internet_exchange,
        }
        return render(request, 'peering/ix/details.html', context)


class IXEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_internetexchange'
    model = InternetExchange
    form = InternetExchangeForm
    template = 'peering/ix/add_edit.html'


class IXDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'peering.delete_internetexchange'
    model = InternetExchange
    return_url = 'peering:internet_exchange_list'


class IXBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'peering.delete_internetexchange'
    model = InternetExchange
    filter = InternetExchangeFilter
    table = InternetExchangeTable


class IXUpdateCommunities(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_internetexchange'
    model = InternetExchange
    form = InternetExchangeCommunityForm
    template = 'peering/ix/communities.html'

    def get(self, request, *args, **kwargs):
        obj = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        form = self.form(instance=obj)

        return render(request, self.template, {
            'object': obj,
            'object_type': self.model._meta.verbose_name,
            'form': form,
            'return_url': self.get_return_url(obj),
        })

    def post(self, request, *args, **kwargs):
        obj = self.get_object(kwargs)
        form = self.form(request.POST, instance=obj)

        if form.is_valid():
            # Clear communities to avoid duplicates
            obj.communities.clear()
            # Add communities one by one
            for community in request.POST.getlist('communities'):
                obj.communities.add(community)
            # Save the object and its linked communities
            obj.save()

            return redirect(self.get_return_url(obj))

        return render(request, self.template, {
            'object': obj,
            'object_type': self.model._meta.verbose_name,
            'form': form,
            'return_url': self.get_return_url(obj),
        })


class IXPeeringSessions(ModelListView):
    filter = InternetExchangePeeringSessionFilter
    filter_form = InternetExchangePeeringSessionFilterFormForIX
    table = InternetExchangePeeringSessionTableForIX
    template = 'peering/ix/sessions.html'

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of InternetExchangePeeringSession objects but they
        # are linked to an IX. So first of all we need to retrieve the IX on
        # which we want to get the peering sessions.
        if 'slug' in kwargs:
            internet_exchange = get_object_or_404(
                InternetExchange, slug=kwargs['slug'])
            queryset = internet_exchange.internetexchangepeeringsession_set.order_by(
                'autonomous_system.asn', 'ip_address')

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}

        # Since we are in the context of an IX we need to keep the reference
        # for it
        if 'slug' in kwargs:
            extra_context.update({
                'internet_exchange': get_object_or_404(InternetExchange,
                                                       slug=kwargs['slug']),
            })

        return extra_context

    def setup_table_columns(self, request, table, kwargs):
        if 'slug' in kwargs:
            internet_exchange = get_object_or_404(
                InternetExchange, slug=kwargs['slug'])

            if internet_exchange.check_bgp_session_states and internet_exchange.router and internet_exchange.router.can_napalm_get_bgp_neighbors_detail():
                if 'session_state' in table.base_columns:
                    table.columns.show('session_state')

        super(IXPeeringSessions, self).setup_table_columns(
            request, table, kwargs)


class IXPeers(ModelListView):
    filter = PeerRecordFilter
    filter_form = PeerRecordFilterForm
    table = PeerRecordTable
    template = 'peering/ix/peers.html'

    def build_queryset(self, request, kwargs):
        queryset = None
        # The queryset needs to be composed of PeerRecord objects but they
        # are linked to an IX. So first of all we need to retrieve the IX on
        # which we want to get the peering sessions.
        if 'slug' in kwargs:
            internet_exchange = get_object_or_404(InternetExchange,
                                                  slug=kwargs['slug'])
            queryset = internet_exchange.get_available_peers()

        return queryset

    def extra_context(self, kwargs):
        extra_context = {}

        # Since we are in the context of an IX we need to keep the reference
        # for it
        if 'slug' in kwargs:
            extra_context.update({
                'internet_exchange': get_object_or_404(InternetExchange,
                                                       slug=kwargs['slug']),
            })

        return extra_context


class IXConfig(View):
    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)

        context = {
            'internet_exchange': internet_exchange,
            'internet_exchange_configuration': internet_exchange.generate_configuration(),
        }

        return render(request, 'peering/ix/configuration.html', context)


class IXUpdateSessionStates(PermissionRequiredMixin, View):
    permission_required = 'peering.change_internetexchangepeeringsession'

    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)
        success = internet_exchange.update_peering_session_states()

        # Message the user based on the result
        if success:
            messages.success(
                request, 'Peering session states successfully updated.')
        else:
            messages.error(
                request, 'Error when trying to update peering session states.')

        return redirect(internet_exchange.get_peering_sessions_list_url())


class InternetExchangePeeringSessionList(ModelListView):
    queryset = InternetExchangePeeringSession.objects.order_by(
        'autonomous_system')
    table = InternetExchangePeeringSessionTable
    filter = InternetExchangePeeringSessionFilter
    filter_form = InternetExchangePeeringSessionFilterForm
    template = 'peering/session/list.html'


class InternetExchangePeeringSessionAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.add_internetexchangepeeringsession'
    model = InternetExchangePeeringSession
    form = InternetExchangePeeringSessionForm
    template = 'peering/session/add_edit.html'

    def get_object(self, kwargs):
        if 'pk' in kwargs:
            return get_object_or_404(self.model, pk=kwargs['pk'])

        return self.model()

    def alter_object(self, obj, request, args, kwargs):
        if 'slug' in kwargs:
            obj.internet_exchange = get_object_or_404(
                InternetExchange, slug=kwargs['slug'])

        return obj

    def get_return_url(self, obj):
        return obj.internet_exchange.get_peering_sessions_list_url()


class InternetExchangePeeringSessionBulkEdit(PermissionRequiredMixin,
                                             BulkEditView):
    permission_required = 'peering.change_internetexchangepeeringsession'
    queryset = InternetExchangePeeringSession.objects.select_related(
        'autonomous_system')
    parent_object = BGPSession
    filter = InternetExchangePeeringSessionFilter
    table = InternetExchangePeeringSessionTable
    form = InternetExchangePeeringSessionBulkEditForm


class InternetExchangePeeringSessionDetails(View):
    def get(self, request, pk):
        peering_session = get_object_or_404(InternetExchangePeeringSession,
                                            pk=pk)
        context = {'peering_session': peering_session}
        return render(request, 'peering/session/details.html', context)


class InternetExchangePeeringSessionEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_internetexchangepeeringsession'
    model = InternetExchangePeeringSession
    form = InternetExchangePeeringSessionForm
    template = 'peering/session/add_edit.html'


class InternetExchangePeeringSessionDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'peering.delete_internetexchangepeeringsession'
    model = InternetExchangePeeringSession

    def get_return_url(self, obj):
        return obj.internet_exchange.get_peering_sessions_list_url()


class InternetExchangePeeringSessionAddFromPeeringDB(PermissionRequiredMixin,
                                                     BulkAddFromDependencyView):
    permission_required = 'peering.add_internetexchangepeeringsession'
    model = InternetExchangePeeringSession
    dependency_model = PeerRecord
    form_model = InternetExchangePeeringSessionForm
    template = 'peering/session/add_from_peeringdb.html'

    def process_dependency_object(self, dependency):
        session6, created6 = InternetExchangePeeringSession.get_from_peeringdb_peer_record(
            dependency, 6)
        session4, created4 = InternetExchangePeeringSession.get_from_peeringdb_peer_record(
            dependency, 4)
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
                    objects.append({
                        'autonomous_system': object.autonomous_system,
                        'internet_exchange': object.internet_exchange,
                        'ip_address': object.ip_address,
                    })
        return objects


class InternetExchangePeeringSessionBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'peering.delete_internetexchangepeeringsession'
    model = InternetExchangePeeringSession
    filter = InternetExchangePeeringSessionFilter
    table = InternetExchangePeeringSessionTableForIX

    def filter_by_extra_context(self, queryset, request, kwargs):
        # If we are on an Internet exchange context, filter the session with
        # the given IX
        if 'internet_exchange_slug' in request.POST:
            internet_exchange_slug = request.POST.get('internet_exchange_slug')
            internet_exchange = get_object_or_404(
                InternetExchange, slug=internet_exchange_slug)
            return queryset.filter(internet_exchange=internet_exchange)
        return queryset


class InternetExchangePeeringSessionDisable(PermissionRequiredMixin, View):
    permission_required = 'peering.change_internetexchangepeeringsession'

    def get(self, request, pk):
        peering_session = get_object_or_404(InternetExchangePeeringSession,
                                            pk=pk)
        peering_session.enabled = False
        peering_session.save()
        return redirect(peering_session.get_absolute_url())


class InternetExchangePeeringSessionEnable(PermissionRequiredMixin, View):
    permission_required = 'peering.change_internetexchangepeeringsession'

    def get(self, request, pk):
        peering_session = get_object_or_404(InternetExchangePeeringSession,
                                            pk=pk)
        peering_session.enabled = True
        peering_session.save()
        return redirect(peering_session.get_absolute_url())


class RouterList(ModelListView):
    queryset = Router.objects.all()
    filter = RouterFilter
    filter_form = RouterFilterForm
    table = RouterTable
    template = 'peering/router/list.html'


class RouterAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.add_router'
    model = Router
    form = RouterForm
    return_url = 'peering:router_list'
    template = 'peering/router/add_edit.html'


class RouterImport(PermissionRequiredMixin, ImportView):
    permission_required = 'peering.add_router'
    form_model = RouterCSVForm
    return_url = 'peering:router_list'


class RouterDetails(View):
    def get(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        internet_exchanges = InternetExchange.objects.filter(router=router)
        context = {
            'router': router,
            'internet_exchanges': internet_exchanges,
        }
        return render(request, 'peering/router/details.html', context)


class RouterEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_router'
    model = Router
    form = RouterForm
    template = 'peering/router/add_edit.html'


class RouterDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'peering.delete_router'
    model = Router
    return_url = 'peering:router_list'


class RouterBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'peering.delete_router'
    model = Router
    filter = RouterFilter
    table = RouterTable


class RoutingPolicyList(ModelListView):
    queryset = RoutingPolicy.objects.all()
    filter = RoutingPolicyFilter
    filter_form = RoutingPolicyFilterForm
    table = RoutingPolicyTable
    template = 'peering/routing-policy/list.html'


class RoutingPolicyAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.add_routingpolicy'
    model = RoutingPolicy
    form = RoutingPolicyForm
    return_url = 'peering:routing_policy_list'
    template = 'peering/routing-policy/add_edit.html'


class RoutingPolicyImport(PermissionRequiredMixin, ImportView):
    permission_required = 'peering.add_routingpolicy'
    form_model = RoutingPolicyCSVForm
    return_url = 'peering:routing_policy_list'


class RoutingPolicyDetails(View):
    def get(self, request, pk):
        routing_policy = get_object_or_404(RoutingPolicy, pk=pk)
        context = {
            'routing_policy': routing_policy,
        }
        return render(request, 'peering/routing-policy/details.html', context)


class RoutingPolicyEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = 'peering.change_routingpolicy'
    model = RoutingPolicy
    form = RoutingPolicyForm
    template = 'peering/routing-policy/add_edit.html'


class RoutingPolicyDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'peering.delete_routingpolicy'
    model = RoutingPolicy
    return_url = 'peering:routing_policy_list'


class RoutingPolicyBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'peering.delete_routingpolicy'
    model = RoutingPolicy
    filter = RoutingPolicyFilter
    table = RoutingPolicyTable


class RoutingPolicyBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = 'peering.change_routingpolicy'
    queryset = RoutingPolicy.objects.all()
    filter = RoutingPolicyFilter
    table = RoutingPolicyTable
    form = RoutingPolicyBulkEditForm


class AsyncRouterPing(View):
    def get(self, request, router_id):
        router = get_object_or_404(Router, id=router_id)

        return HttpResponse(json.dumps({
            'status': 'success' if router.test_napalm_connection() else 'error'
        }))


class AsyncRouterDiff(View):
    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)
        changes = internet_exchange.router.set_napalm_configuration(
            internet_exchange.generate_configuration())

        return HttpResponse(json.dumps({
            'changed': True if changes else False,
            'changes': changes,
        }))


class AsyncRouterSave(View):
    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)
        changes = internet_exchange.router.set_napalm_configuration(
            internet_exchange.generate_configuration(), True)

        return HttpResponse(json.dumps({
            'success': True if changes else False,
        }))
