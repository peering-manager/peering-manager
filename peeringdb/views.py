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
            "fac_count": Facility.objects.count(),
            "ix_count": InternetExchange.objects.count(),
            "ixfac_count": InternetExchangeFacility.objects.count(),
            "ixlan_count": IXLan.objects.count(),
            "ixlanpfx_count": IXLanPrefix.objects.count(),
            "net_count": Network.objects.count(),
            "poc_count": NetworkContact.objects.count(),
            "netfac_count": NetworkFacility.objects.count(),
            "netixlan_count": NetworkContact.objects.count(),
            "org_count": Organization.objects.count(),
        }

        return render(request, "peeringdb/cache.html", context)
