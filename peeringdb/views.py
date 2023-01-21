from django.contrib import messages
from django.shortcuts import redirect, render, reverse
from django.views.generic import View

from .models import (
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


class CacheManagementView(View):
    def get(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            messages.error(
                request, "You do not have the permissions to manage PeeringDB's cache."
            )
            return redirect(reverse("home"))

        last_synchronization = PeeringDB().get_last_synchronization()
        sync_time = last_synchronization.time if last_synchronization else 0

        context = {
            "last_sync_time": sync_time,
            "counts": [
                {
                    "Facilities": Facility.objects.count(),
                    "Internet Exchanges": InternetExchange.objects.count(),
                    "Internet Exchange Facilities": InternetExchangeFacility.objects.count(),
                },
                {
                    "Internet Exchange LANs": IXLan.objects.count(),
                    "Internet Exchange LAN Prefixes": IXLanPrefix.objects.count(),
                    "Networks": Network.objects.count(),
                },
                {
                    "Network Contacts": NetworkContact.objects.count(),
                    "Network Facilities": NetworkFacility.objects.count(),
                    "Network Internet Exchange LANs": NetworkContact.objects.count(),
                },
                {
                    "Organizations": Organization.objects.count(),
                },
            ],
        }

        return render(request, "peeringdb/cache.html", context)
