from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, reverse
from django.views.generic import View

from .http import PeeringDB
from .models import Network, NetworkIXLAN, PeerRecord


class CacheManagementView(View):
    def get(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, "You do not have the rights to index peer records.")
            return redirect(reverse("home"))

        last_synchronization = PeeringDB().get_last_synchronization()
        sync_time = last_synchronization.time if last_synchronization else 0

        context = {
            "last_sync_time": sync_time,
            "peeringdb_network_count": Network.objects.count(),
            "peeringdb_networkixlan_count": NetworkIXLAN.objects.count(),
            "peer_record_count": PeerRecord.objects.count(),
        }
        return render(request, "peeringdb/cache.html", context)


class BuildCacheView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff and not request.user.is_superuser:
            api = PeeringDB()
            api.update_local_database(api.get_last_sync_time())
            messages.success(request, "Successfully built the local cache.")
        else:
            messages.error(
                request, "You do not have the rights to build the local cache."
            )

        return redirect(reverse("peeringdb:cache_management"))


class ClearCacheView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff and not request.user.is_superuser:
            PeeringDB().clear_local_database()
            messages.success(request, "Successfully cleared the local cache.")
        else:
            messages.error(
                request, "You do not have the rights to clear the local cache."
            )

        return redirect(reverse("peeringdb:cache_management"))


class IndexPeerRecords(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff and not request.user.is_superuser:
            PeeringDB().force_peer_records_discovery()
            messages.success(request, "Successfully indexed peer records.")
        else:
            messages.error(request, "You do not have the rights to index peer records.")

        return redirect(reverse("peeringdb:cache_management"))
