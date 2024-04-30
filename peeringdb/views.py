from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render, reverse
from django.views.generic import View

from peering.models import InternetExchange as Ixp
from peering_manager.views.generic import ObjectListView, PermissionRequiredMixin

from .filtersets import NetworkIXLanFilterSet
from .forms import NetworkIXLanFilterForm, SendEmailToNetwork
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

        for ixp in Ixp.objects.all():
            queryset = queryset | ixp.get_available_peers()

        return queryset


class EmailNetwork(PermissionRequiredMixin, View):
    permission_required = "peering.send_email"

    def get(self, request, *args, **kwargs):
        form = SendEmailToNetwork()
        form.fields["recipients"].choices = []
        form.fields["cc"].choices = settings.EMAIL_CC_CONTACTS
        return render(
            request, "peering/provisioning/email_network.html", {"form": form}
        )

    def post(self, request, *args, **kwargs):
        form = SendEmailToNetwork(request.POST)
        try:
            network_id = int(request.POST.get("network"))
        except ValueError:
            messages.error("Unable to send the e-mail, AS not available.")
            return redirect("peeringdb:email_network")

        # Guess the set of possible recipients given the network ID
        form.fields["recipients"].choices = [
            (contact.email, contact.email)
            for contact in NetworkContact.objects.filter(net_id=network_id)
        ]
        form.fields["cc"].choices = settings.EMAIL_CC_CONTACTS

        if form.is_valid():
            mail = EmailMessage(
                subject=form.cleaned_data["subject"],
                body=form.cleaned_data["body"],
                from_email=settings.SERVER_EMAIL,
                to=form.cleaned_data["recipients"],
                cc=form.cleaned_data["cc"],
            )
            sent = mail.send()
            if sent == 1:
                messages.success(request, "E-mail sent.")
            else:
                messages.error(request, "Unable to send the e-mail.")

        return redirect("peeringdb:email_network")
