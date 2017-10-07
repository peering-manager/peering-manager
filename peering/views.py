from __future__ import unicode_literals

from jinja2 import Template

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from django_tables2 import RequestConfig

from .forms import AutonomousSystemForm, AutonomousSystemCSVForm, ConfigurationTemplateForm, InternetExchangeForm, InternetExchangeCSVForm, PeeringSessionForm
from .models import AutonomousSystem, ConfigurationTemplate, InternetExchange, PeeringSession
from .tables import AutonomousSystemTable, ConfigurationTemplateTable, InternetExchangeTable, PeeringSessionTable
from utils.views import AddOrEditView, DeleteView, ImportView


class ASList(View):
    def get(self, request):
        autonomous_systems = AutonomousSystemTable(
            AutonomousSystem.objects.order_by('asn'))
        RequestConfig(request).configure(autonomous_systems)
        context = {
            'autonomous_systems': autonomous_systems
        }
        return render(request, 'peering/as/list.html', context)


class ASAdd(AddOrEditView):
    model = AutonomousSystem
    form = AutonomousSystemForm
    return_url = 'peering:as_list'
    template = 'peering/as/add_edit.html'


class AutonomousSystemImport(ImportView):
    form_model = AutonomousSystemCSVForm
    return_url = 'peering:as_list'


class ASDetails(View):
    def get(self, request, asn):
        autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)
        context = {
            'autonomous_system': autonomous_system,
            'internet_exchanges': autonomous_system.get_internet_exchanges(),
            'peering_sessions_count': autonomous_system.get_peering_sessions_count(),
        }
        return render(request, 'peering/as/details.html', context)


class ASEdit(AddOrEditView):
    model = AutonomousSystem
    form = AutonomousSystemForm
    template = 'peering/as/add_edit.html'


class ASDelete(DeleteView):
    model = AutonomousSystem
    return_url = 'peering:as_list'


class ConfigTemplateList(View):
    def get(self, request):
        configuration_templates = ConfigurationTemplateTable(
            ConfigurationTemplate.objects.all())
        RequestConfig(request).configure(configuration_templates)
        context = {
            'configuration_templates': configuration_templates
        }
        return render(request, 'peering/config/list.html', context)


class ConfigTemplateAdd(AddOrEditView):
    model = ConfigurationTemplate
    form = ConfigurationTemplateForm
    return_url = 'peering:configuration_template_list'


class ConfigTemplateDetails(View):
    def get(self, request, id):
        configuration_template = get_object_or_404(
            ConfigurationTemplate, id=id)
        internet_exchanges = InternetExchange.objects.filter(
            configuration_template=configuration_template)
        context = {
            'configuration_template': configuration_template,
            'internet_exchanges': internet_exchanges,
        }
        return render(request, 'peering/config/details.html', context)


class ConfigTemplateEdit(AddOrEditView):
    model = ConfigurationTemplate
    form = ConfigurationTemplateForm


class ConfigTemplateDelete(DeleteView):
    model = ConfigurationTemplate
    return_url = 'peering:configuration_template_list'


class IXList(View):
    def get(self, request):
        internet_exchanges = InternetExchangeTable(
            InternetExchange.objects.order_by('name'))
        RequestConfig(request).configure(internet_exchanges)
        context = {'internet_exchanges': internet_exchanges}
        return render(request, 'peering/ix/list.html', context)


class IXAdd(AddOrEditView):
    model = InternetExchange
    form = InternetExchangeForm
    return_url = 'peering:ix_list'
    template = 'peering/ix/add_edit.html'


class InternetExchangeImport(ImportView):
    form_model = InternetExchangeCSVForm
    return_url = 'peering:ix_list'


class IXDetails(View):
    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)
        peering_sessions = PeeringSessionTable(internet_exchange.peeringsession_set.order_by(
            'autonomous_system.asn', 'ip_address'))
        RequestConfig(request).configure(peering_sessions)
        context = {
            'internet_exchange': internet_exchange,
            'peering_sessions': peering_sessions,
            'autonomous_systems_count': internet_exchange.get_autonomous_systems_count(),
            'peering_sessions_count': internet_exchange.get_peering_sessions_count(),
        }
        return render(request, 'peering/ix/details.html', context)


class IXEdit(AddOrEditView):
    model = InternetExchange
    form = InternetExchangeForm
    template = 'peering/ix/add_edit.html'


class IXDelete(DeleteView):
    model = InternetExchange
    return_url = 'peering:ix_list'


class IXConfig(LoginRequiredMixin, View):
    def get(self, request, slug):
        internet_exchange = get_object_or_404(InternetExchange, slug=slug)
        peering_sessions = internet_exchange.peeringsession_set.all()

        peering_sessions6 = []
        peering_sessions4 = []

        # Sort peering sessions based on IP protocol version
        for session in peering_sessions:
            session_dict = session.to_dict()
            if session_dict['ip_version'] == 6:
                peering_sessions6.append(session_dict)
            if session_dict['ip_version'] == 4:
                peering_sessions4.append(session_dict)

        peering_groups = [
            {'name': 'ipv6', 'sessions': peering_sessions6},
            {'name': 'ipv4', 'sessions': peering_sessions4},
        ]

        values = {
            'internet_exchange': internet_exchange,
            'peering_groups': peering_groups,
        }

        # Load and render the template using Jinja2
        configuration_template = Template(
            internet_exchange.configuration_template.template)
        configuration = configuration_template.render(values)

        context = {
            'internet_exchange': internet_exchange,
            'internet_exchange_configuration': configuration,
        }

        return render(request, 'peering/ix/configuration.html', context)


class PeeringSessionAdd(AddOrEditView):
    model = PeeringSession
    form = PeeringSessionForm
    template = 'peering/session/add_edit.html'

    def get_object(self, kwargs):
        if 'id' in kwargs:
            return get_object_or_404(self.model, id=kwargs['id'])

        return self.model()

    def alter_object(self, obj, request, args, kwargs):
        if 'slug' in kwargs:
            obj.internet_exchange = get_object_or_404(
                InternetExchange, slug=kwargs['slug'])

        return obj

    def get_return_url(self, obj):
        return obj.internet_exchange.get_absolute_url()


class PeeringSessionDetails(View):
    def get(self, request, id):
        peering_session = get_object_or_404(PeeringSession, id=id)
        context = {'peering_session': peering_session}
        return render(request, 'peering/session/details.html', context)


class PeeringSessionEdit(AddOrEditView):
    model = PeeringSession
    form = PeeringSessionForm
    template = 'peering/session/add_edit.html'


class PeeringSessionDelete(DeleteView):
    model = PeeringSession

    def get_return_url(self, obj):
        return obj.internet_exchange.get_absolute_url()
