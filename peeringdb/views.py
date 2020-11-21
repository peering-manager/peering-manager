from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render, reverse
from django.views.generic import View

from utils.views import BulkEditView

from .filters import PeerRecordFilterSet
from .forms import PeerRecordBulkEditForm
from .http import PeeringDB
from .models import Contact, Network, NetworkIXLAN, PeerRecord
from .tables import PeerRecordTable


class CacheManagementView(View):
    def get(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, "You do not have the rights to index peer records.")
            return redirect(reverse("home"))

        last_synchronization = PeeringDB().get_last_synchronization()
        sync_time = last_synchronization.time if last_synchronization else 0

        context = {
            "last_sync_time": sync_time,
            "peeringdb_contact_count": Contact.objects.count(),
            "peeringdb_network_count": Network.objects.count(),
            "peeringdb_networkixlan_count": NetworkIXLAN.objects.count(),
            "peer_record_count": PeerRecord.objects.count(),
        }
        return render(request, "peeringdb/cache.html", context)


class PeerRecordBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "peeringdb.change_peerrecord"
    queryset = PeerRecord.objects.all()
    filter = PeerRecordFilterSet
    table = PeerRecordTable
    form = PeerRecordBulkEditForm
