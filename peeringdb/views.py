from django.contrib import messages
from django.shortcuts import redirect, render, reverse
from django.views.generic import View

from peering.models import InternetExchange as IXP
from peering_manager.views.generic import ObjectListView

from .filtersets import NetworkIXLanFilterSet
from .forms import NetworkIXLanFilterForm
from .models import (
    Campus,
    Carrier,
    CarrierFacility,
    Facility,
    InternetExchange,
    InternetExchangeFacility,
    IXLan,
    IXLanPrefix,
    Network,
    NetworkContact,
    NetworkFacility,
    NetworkIXLan,
    Organization,
)
from .sync import PeeringDB
from .tables import NetworkIXLanTable


class CacheManagementView(View):
    def get(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            messages.error(
                request, "You do not have the permissions to manage PeeringDB's cache."
            )
            return redirect(reverse("home"))

        last_synchronisation = PeeringDB().get_last_synchronisation()
        sync_time = last_synchronisation.time if last_synchronisation else 0

        context = {
            "last_sync_time": sync_time,
            "counts": [
                {
                    "Campuses": Campus.objects.count(),
                    "Carriers": Carrier.objects.count(),
                    "Carrier Facilities": CarrierFacility.objects.count(),
                    "Facilities": Facility.objects.count(),
                },
                {
                    "Internet Exchanges": InternetExchange.objects.count(),
                    "Internet Exchange Facilities": InternetExchangeFacility.objects.count(),
                    "Internet Exchange LANs": IXLan.objects.count(),
                    "Internet Exchange LAN Prefixes": IXLanPrefix.objects.count(),
                },
                {
                    "Networks": Network.objects.count(),
                    "Network Contacts": NetworkContact.objects.count(),
                    "Network Facilities": NetworkFacility.objects.count(),
                    "Network Internet Exchange LANs": NetworkIXLan.objects.count(),
                },
                {"Organizations": Organization.objects.count()},
            ],
        }

        return render(request, "peeringdb/cache.html", context)


class AvailableIXPPeers(ObjectListView):
    permission_required = "peering.view_internetexchange"
    filterset = NetworkIXLanFilterSet
    filterset_form = NetworkIXLanFilterForm
    table = NetworkIXLanTable
    template_name = "peering/provisioning/peers.html"

    def get_queryset(self, request):
        queryset = NetworkIXLan.objects.none()

        for ixp in IXP.objects.all():
            queryset = queryset | ixp.get_available_peers()

        return queryset
