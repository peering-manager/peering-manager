from __future__ import unicode_literals

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from django_tables2 import RequestConfig

from .forms import AutonomousSystemForm, ConfirmationForm, InternetExchangeForm, PeeringSessionForm
from .models import AutonomousSystem, InternetExchange, PeeringSession
from .tables import AutonomousSystemTable, InternetExchangeTable, PeeringSessionTable


def home(request):
    context = {
        'autonomous_systems_count': AutonomousSystem.objects.count(),
        'internet_exchanges_count': InternetExchange.objects.count(),
        'peering_sessions_count': PeeringSession.objects.count(),
    }
    return render(request, 'home.html', context)


def as_list(request):
    autonomous_systems = AutonomousSystemTable(
        AutonomousSystem.objects.order_by('asn'))
    RequestConfig(request).configure(autonomous_systems)
    context = {
        'autonomous_systems': autonomous_systems
    }

    return render(request, 'peering/as_list.html', context)


def as_add(request):
    if request.method == 'POST':
        form = AutonomousSystemForm(request.POST)
        if form.is_valid():
            autonomous_system = form.save()
            return redirect('peering:as_details', asn=autonomous_system.asn)
    else:
        form = AutonomousSystemForm()

    return render(request, 'peering/as_add.html', {'form': form})


def as_details(request, asn):
    autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)

    context = {
        'autonomous_system': autonomous_system,
        'internet_exchanges': autonomous_system.get_internet_exchanges(),
        'peering_sessions_count': autonomous_system.get_peering_sessions_count(),
    }

    return render(request, 'peering/as_details.html', context)


def as_edit(request, asn):
    autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)

    if request.method == 'POST':
        form = AutonomousSystemForm(request.POST, instance=autonomous_system)
        if form.is_valid():
            autonomous_system = form.save()
            return redirect('peering:as_details', asn=asn)
    else:
        form = AutonomousSystemForm(instance=autonomous_system)

    context = {
        'form': form,
        'autonomous_system': autonomous_system,
    }

    return render(request, 'peering/as_edit.html', context)


def as_delete(request, asn):
    autonomous_system = get_object_or_404(AutonomousSystem, asn=asn)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            autonomous_system.delete()
            return redirect('peering:as_list')
    else:
        form = ConfirmationForm(initial=request.GET)

    context = {
        'form': form,
        'autonomous_system': autonomous_system,
    }

    return render(request, 'peering/as_delete.html', context)


def ix_list(request):
    internet_exchanges = InternetExchangeTable(
        InternetExchange.objects.order_by('name'))
    RequestConfig(request).configure(internet_exchanges)
    context = {'internet_exchanges': internet_exchanges}

    return render(request, 'peering/ix_list.html', context)


def ix_add(request):
    if request.method == 'POST':
        form = InternetExchangeForm(request.POST)
        if form.is_valid():
            internet_exchange = form.save()
            return redirect('peering:ix_details', slug=internet_exchange.slug)
    else:
        form = InternetExchangeForm()

    return render(request, 'peering/ix_add.html', {'form': form})


def ix_details(request, slug):
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

    return render(request, 'peering/ix_details.html', context)


def ix_edit(request, slug):
    internet_exchange = get_object_or_404(InternetExchange, slug=slug)

    if request.method == 'POST':
        form = InternetExchangeForm(request.POST, instance=internet_exchange)
        if form.is_valid():
            internet_exchange = form.save()
            return redirect('peering:ix_details', slug=slug)
    else:
        form = InternetExchangeForm(instance=internet_exchange)

    context = {
        'form': form,
        'internet_exchange': internet_exchange,
    }

    return render(request, 'peering/ix_edit.html', context)


def ix_delete(request, slug):
    internet_exchange = get_object_or_404(InternetExchange, slug=slug)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            internet_exchange.delete()
            return redirect('peering:ix_list')
    else:
        form = ConfirmationForm(initial=request.GET)

    context = {
        'form': form,
        'internet_exchange': internet_exchange,
    }

    return render(request, 'peering/ix_delete.html', context)


def peering_session_add(request, slug):
    internet_exchange = get_object_or_404(InternetExchange, slug=slug)

    if request.method == 'POST':
        form = PeeringSessionForm(request.POST)
        if form.is_valid():
            return redirect('peering:ix_details', slug=slug)
    else:
        form = PeeringSessionForm(
            initial={'internet_exchange': internet_exchange.id})

    context = {
        'form': form,
        'internet_exchange': internet_exchange,
    }

    return render(request, 'peering/peering_session_add.html', context)


def peering_session_details(request, id):
    peering_session = get_object_or_404(PeeringSession, id=id)
    context = {'peering_session': peering_session}
    return render(request, 'peering/peering_session_details.html', context)


def peering_session_edit(request, id):
    peering_session = get_object_or_404(PeeringSession, id=id)

    if request.method == 'POST':
        form = PeeringSessionForm(request.POST, instance=peering_session)
        if form.is_valid():
            peering_session = form.save()
            return redirect('peering:peering_session_details', id=id)
    else:
        form = PeeringSessionForm(instance=peering_session)

    context = {
        'form': form,
        'peering_session': peering_session,
    }

    return render(request, 'peering/peering_session_edit.html', context)


def peering_session_delete(request, id):
    peering_session = get_object_or_404(PeeringSession, id=id)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            internet_exchange.delete()
            return redirect('peering:ix_details', slug=peering_session.internet_exchange.slug)
    else:
        form = ConfirmationForm(initial=request.GET)

    context = {
        'form': form,
        'peering_session': peering_session,
    }

    return render(request, 'peering/peering_session_delete.html', context)
