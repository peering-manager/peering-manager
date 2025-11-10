from django.contrib import messages
from django.shortcuts import redirect, render, reverse
from django.views.generic import View

from ..models import (
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
from ..sync import PeeringDB

__all__ = ("CacheManagementView",)


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
