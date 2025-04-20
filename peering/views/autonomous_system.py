from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from extras.views import ObjectConfigContextView
from peering_manager.views.generic import (
    BulkDeleteView,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
    PermissionRequiredMixin,
)
from peeringdb.tables import NetworkIXLanTable
from utils.views import ViewTab, register_model_view

from ..filtersets import (
    AutonomousSystemFilterSet,
    DirectPeeringSessionFilterSet,
    InternetExchangePeeringSessionFilterSet,
)
from ..forms import (
    AutonomousSystemEmailForm,
    AutonomousSystemFilterForm,
    AutonomousSystemForm,
    DirectPeeringSessionFilterForm,
    InternetExchangePeeringSessionFilterForm,
)
from ..models import (
    AutonomousSystem,
    DirectPeeringSession,
    InternetExchangePeeringSession,
    NetworkIXLan,
)
from ..tables import (
    AutonomousSystemTable,
    DirectPeeringSessionTable,
    InternetExchangePeeringSessionTable,
)

__all__ = (
    "AutonomousSystemBulkDelete",
    "AutonomousSystemConfigContext",
    "AutonomousSystemDelete",
    "AutonomousSystemDirectPeeringSessions",
    "AutonomousSystemEdit",
    "AutonomousSystemEmail",
    "AutonomousSystemInternetExchangesPeeringSessions",
    "AutonomousSystemList",
    "AutonomousSystemPeeringDB",
    "AutonomousSystemPeers",
    "AutonomousSystemView",
)


@register_model_view(AutonomousSystem, name="list", path="", detail=False)
class AutonomousSystemList(ObjectListView):
    permission_required = "peering.view_autonomoussystem"
    queryset = (
        AutonomousSystem.objects.defer("prefixes")
        .annotate(
            directpeeringsession_count=Count("directpeeringsession", distinct=True),
            internetexchangepeeringsession_count=Count(
                "internetexchangepeeringsession", distinct=True
            ),
        )
        .order_by("affiliated", "asn")
    )
    filterset = AutonomousSystemFilterSet
    filterset_form = AutonomousSystemFilterForm
    table = AutonomousSystemTable
    template_name = "peering/autonomoussystem/list.html"


@register_model_view(AutonomousSystem)
class AutonomousSystemView(ObjectView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")

    def get_extra_context(self, request, instance):
        shared_internet_exchanges = {}

        if not request.user.is_anonymous and request.user.preferences.get("context.as"):
            try:
                affiliated = AutonomousSystem.objects.get(
                    pk=request.user.preferences.get("context.as")
                )
            except AutonomousSystem.DoesNotExist:
                affiliated = None

            for ix in instance.get_shared_internet_exchange_points(affiliated):
                shared_internet_exchanges[ix] = instance.get_missing_peering_sessions(
                    affiliated, ix
                )

        return {"shared_internet_exchanges": shared_internet_exchanges}


@register_model_view(model=AutonomousSystem, name="add", detail=False)
@register_model_view(model=AutonomousSystem, name="edit")
class AutonomousSystemEdit(ObjectEditView):
    queryset = AutonomousSystem.objects.defer("prefixes")
    form = AutonomousSystemForm
    template_name = "peering/autonomoussystem/edit.html"


@register_model_view(AutonomousSystem, name="delete")
class AutonomousSystemDelete(ObjectDeleteView):
    permission_required = "peering.delete_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")


@register_model_view(AutonomousSystem, name="bulk_delete", path="delete", detail=False)
class AutonomousSystemBulkDelete(BulkDeleteView):
    queryset = AutonomousSystem.objects.defer("prefixes")
    filterset = AutonomousSystemFilterSet
    table = AutonomousSystemTable


@register_model_view(AutonomousSystem, name="configcontext", path="config-context")
class AutonomousSystemConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    base_template = "peering/autonomoussystem/_base.html"


@register_model_view(AutonomousSystem, name="peeringdb")
class AutonomousSystemPeeringDB(ObjectView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    template_name = "peering/autonomoussystem/peeringdb.html"
    tab = ViewTab(label="PeeringDB")

    def get_extra_context(self, request, instance):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
            facilities = instance.get_peeringdb_shared_facilities(affiliated)
        except AutonomousSystem.DoesNotExist:
            facilities = []

        return {"contacts": instance.peeringdb_contacts, "facilities": facilities}


@register_model_view(
    AutonomousSystem, name="direct_peering_sessions", path="direct-peering-sessions"
)
class AutonomousSystemDirectPeeringSessions(ObjectChildrenView):
    permission_required = (
        "peering.view_autonomoussystem",
        "peering.view_directpeeringsession",
    )
    queryset = AutonomousSystem.objects.defer("prefixes")
    child_model = DirectPeeringSession
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template_name = "peering/autonomoussystem/direct_peering_sessions.html"
    tab = ViewTab(
        label="Direct Peering Sessions",
        permission="peering.view_directpeeringsession",
        weight=2000,
    )

    def get_children(self, request, parent):
        return (
            parent.get_direct_peering_sessions()
            .prefetch_related("bgp_group")
            .order_by("bgp_group", "relationship", "ip_address")
        )


@register_model_view(
    AutonomousSystem,
    name="internet_exchange_peering_sessions",
    path="ix-peering-sessions",
)
class AutonomousSystemInternetExchangesPeeringSessions(ObjectChildrenView):
    permission_required = (
        "peering.view_autonomoussystem",
        "peering.view_internetexchangepeeringsession",
    )
    queryset = AutonomousSystem.objects.defer("prefixes")
    child_model = InternetExchangePeeringSession
    filterset = InternetExchangePeeringSessionFilterSet
    filterset_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template_name = "peering/autonomoussystem/internet_exchange_peering_sessions.html"
    tab = ViewTab(
        label="IX Peering Sessions",
        permission="peering.view_internetexchangepeeringsession",
        weight=3000,
    )

    def get_children(self, request, parent):
        return (
            parent.get_ixp_peering_sessions()
            .prefetch_related("ixp_connection")
            .order_by("ixp_connection", "ip_address")
        )


@register_model_view(AutonomousSystem, name="peers")
class AutonomousSystemPeers(ObjectChildrenView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.defer("prefixes")
    child_model = NetworkIXLan
    table = NetworkIXLanTable
    template_name = "peering/autonomoussystem/peers.html"
    tab = ViewTab(label="Available Sessions", weight=4000)

    def get_children(self, request, parent):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            affiliated = None

        return parent.get_missing_peering_sessions(affiliated)


@register_model_view(AutonomousSystem, name="email")
class AutonomousSystemEmail(PermissionRequiredMixin, View):
    permission_required = "peering.send_email"
    tab = ViewTab(label="E-mail", permission="peering.send_email", weight=5000)

    def get(self, request, *args, **kwargs):
        instance = get_object_or_404(AutonomousSystem, pk=kwargs["pk"])

        if not instance.can_receive_email:
            return redirect(instance.get_absolute_url())

        form = AutonomousSystemEmailForm()
        form.fields["recipient"].choices = instance.get_contact_email_addresses()
        form.fields["cc"].choices = instance.get_cc_email_contacts()
        return render(
            request,
            "peering/autonomoussystem/email.html",
            {"instance": instance, "form": form, "tab": self.tab},
        )

    def post(self, request, *args, **kwargs):
        instance = get_object_or_404(AutonomousSystem, pk=kwargs["pk"])

        if not instance.can_receive_email:
            redirect(instance.get_absolute_url())

        form = AutonomousSystemEmailForm(request.POST)
        form.fields["recipient"].choices = instance.get_contact_email_addresses()
        form.fields["cc"].choices = instance.get_cc_email_contacts()

        if form.is_valid():
            mail = EmailMessage(
                subject=form.cleaned_data["subject"],
                body=form.cleaned_data["body"],
                from_email=settings.SERVER_EMAIL,
                to=form.cleaned_data["recipient"],
                cc=form.cleaned_data["cc"],
            )
            sent = mail.send()
            if sent == 1:
                messages.success(request, "Email sent.")
            else:
                messages.error(request, "Unable to send the email.")

        return redirect(instance.get_absolute_url())
