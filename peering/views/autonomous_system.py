from typing import Any

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import View

from extras.constants import EMAIL_SENT_JOURNAL_TEMPLATE
from extras.enums import JournalEntryKind
from extras.models import JournalEntry
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
    AutonomousSystemPrefixFilterForm,
    DirectPeeringSessionFilterForm,
    InternetExchangePeeringSessionFilterForm,
)
from ..functions import build_irr_as_set_command, parse_irr_as_set
from ..models import (
    AutonomousSystem,
    DirectPeeringSession,
    InternetExchangePeeringSession,
    NetworkIXLan,
)
from ..tables import (
    AutonomousSystemPrefixTable,
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
    "AutonomousSystemPrefixes",
    "AutonomousSystemView",
)


@register_model_view(AutonomousSystem, name="list", path="", detail=False)
class AutonomousSystemList(ObjectListView):
    permission_required = "peering.view_autonomoussystem"
    queryset = (
        AutonomousSystem.objects.all()
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
    queryset = AutonomousSystem.objects.all()

    def get_extra_context(self, request, instance):
        shared_internet_exchanges = {}

        if not request.user.is_anonymous and request.user.preferences.get("context.as"):
            try:
                affiliated = AutonomousSystem.objects.get(
                    pk=request.user.preferences.get("context.as")
                )
            except AutonomousSystem.DoesNotExist:
                return {"shared_internet_exchanges": shared_internet_exchanges}

            ixlans_with_missing_sessions = set(
                instance.get_missing_peering_sessions(affiliated).values_list(
                    "ixlan_id", flat=True
                )
            )

            for ixp in instance.get_shared_internet_exchange_points(affiliated):
                shared_internet_exchanges[ixp] = (
                    ixp.peeringdb_ixlan_id in ixlans_with_missing_sessions
                )

        return {"shared_internet_exchanges": shared_internet_exchanges}


@register_model_view(model=AutonomousSystem, name="add", detail=False)
@register_model_view(model=AutonomousSystem, name="edit")
class AutonomousSystemEdit(ObjectEditView):
    queryset = AutonomousSystem.objects.all()
    form = AutonomousSystemForm
    template_name = "peering/autonomoussystem/edit.html"


@register_model_view(AutonomousSystem, name="delete")
class AutonomousSystemDelete(ObjectDeleteView):
    permission_required = "peering.delete_autonomoussystem"
    queryset = AutonomousSystem.objects.all()


@register_model_view(AutonomousSystem, name="bulk_delete", path="delete", detail=False)
class AutonomousSystemBulkDelete(BulkDeleteView):
    queryset = AutonomousSystem.objects.all()
    filterset = AutonomousSystemFilterSet
    table = AutonomousSystemTable


@register_model_view(AutonomousSystem, name="configcontext", path="config-context")
class AutonomousSystemConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.all()
    base_template = "peering/autonomoussystem/_base.html"


@register_model_view(AutonomousSystem, name="peeringdb")
class AutonomousSystemPeeringDB(ObjectView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.all()
    template_name = "peering/autonomoussystem/peeringdb.html"
    tab = ViewTab(
        label="PeeringDB", visible=lambda instance: bool(instance.peeringdb_network)
    )

    def get_extra_context(self, request, instance):
        try:
            affiliated = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
            facilities = instance.get_peeringdb_shared_facilities(affiliated)
        except AutonomousSystem.DoesNotExist:
            facilities = []

        return {"contacts": instance.peeringdb_contacts, "facilities": facilities}


@register_model_view(AutonomousSystem, name="prefixes")
class AutonomousSystemPrefixes(ObjectView):
    permission_required = "peering.view_autonomoussystem"
    queryset = AutonomousSystem.objects.all()
    template_name = "peering/autonomoussystem/prefixes.html"
    tab = ViewTab(label="Prefixes", weight=1500)

    def get_extra_context(self, request, instance):
        family: str = request.GET.get("family", "")
        search: str = request.GET.get("q", "").strip().lower()

        prefixes_data: dict[str, list[dict[str, Any]]] = instance.prefixes or {
            "ipv6": [],
            "ipv4": [],
        }
        ipv6_prefixes: list[dict[str, Any]] = prefixes_data.get("ipv6", [])
        ipv4_prefixes: list[dict[str, Any]] = prefixes_data.get("ipv4", [])

        all_prefixes: list[dict[str, Any]] = []
        for af, prefix_list in [("ipv6", ipv6_prefixes), ("ipv4", ipv4_prefixes)]:
            if family and family != af:
                continue
            filtered = (
                [p for p in prefix_list if p["prefix"].lower().startswith(search)]
                if search
                else prefix_list
            )
            all_prefixes.extend({**p, "family": af} for p in filtered)

        filter_form = AutonomousSystemPrefixFilterForm(request.GET)
        table = AutonomousSystemPrefixTable(all_prefixes, user=request.user)
        table.configure(request)

        irr_commands: list[dict[str, str]] = []
        for source, as_set in parse_irr_as_set(
            asn=instance.asn, irr_as_set=instance.irr_as_set
        ):
            for af, af_label, override in [
                (6, "IPv6", instance.irr_ipv6_prefixes_args_override),
                (4, "IPv4", instance.irr_ipv4_prefixes_args_override),
            ]:
                cmd = build_irr_as_set_command(
                    as_set=as_set,
                    source=source,
                    address_family=af,
                    irr_sources_override=instance.irr_sources_override,
                    **{f"irr_ipv{af}_prefixes_args_override": override},
                )
                irr_commands.append(
                    {
                        "family": af_label,
                        "as_set": as_set,
                        "source": source,
                        "command": " ".join(cmd),
                    }
                )

        return {
            "table": table,
            "filter_form": filter_form,
            "ipv6_count": len(ipv6_prefixes),
            "ipv4_count": len(ipv4_prefixes),
            "total_count": len(ipv6_prefixes) + len(ipv4_prefixes),
            "irr_commands": irr_commands,
            "as_list": sorted(instance.as_list),
        }


@register_model_view(
    AutonomousSystem, name="direct_peering_sessions", path="direct-peering-sessions"
)
class AutonomousSystemDirectPeeringSessions(ObjectChildrenView):
    permission_required = (
        "peering.view_autonomoussystem",
        "peering.view_directpeeringsession",
    )
    queryset = AutonomousSystem.objects.all()
    child_model = DirectPeeringSession
    filterset = DirectPeeringSessionFilterSet
    filterset_form = DirectPeeringSessionFilterForm
    table = DirectPeeringSessionTable
    template_name = "peering/autonomoussystem/direct_peering_sessions.html"
    tab = ViewTab(
        label="Direct Peering Sessions",
        badge=lambda instance: instance.get_direct_peering_sessions().count(),
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
    queryset = AutonomousSystem.objects.all()
    child_model = InternetExchangePeeringSession
    filterset = InternetExchangePeeringSessionFilterSet
    filterset_form = InternetExchangePeeringSessionFilterForm
    table = InternetExchangePeeringSessionTable
    template_name = "peering/autonomoussystem/internet_exchange_peering_sessions.html"
    tab = ViewTab(
        label="IX Peering Sessions",
        badge=lambda instance: instance.get_ixp_peering_sessions().count(),
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
    queryset = AutonomousSystem.objects.all()
    child_model = NetworkIXLan
    table = NetworkIXLanTable
    template_name = "peering/autonomoussystem/peers.html"
    tab = ViewTab(
        label="Available Sessions",
        weight=4000,
        visible=lambda instance: bool(instance.peeringdb_network),
    )

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

            try:
                sent = mail.send()
                error_message = None
            except Exception as exc:
                sent = 0
                error_message = f"Unable to send e-mail: {exc!s}"

            if error_message:
                message = mark_safe(
                    "Unable to send the e-mail, see "
                    f'<a href="{reverse("peering:autonomoussystem_journal", kwargs={"pk": instance.pk})}">'
                    "journal</a> for more details."
                )
                messages.error(request, message)
            elif not sent:
                message = "E-mail not sent, no recipients."
                messages.warning(request, message)
            else:
                message = "E-mail sent."
                messages.success(request, message)

            JournalEntry.log(
                object=instance,
                comments=EMAIL_SENT_JOURNAL_TEMPLATE.format(
                    message=error_message or message,
                    recipients=", ".join(mail.to),
                    cc=", ".join(mail.cc),
                    sender=mail.from_email,
                    subject=mail.subject,
                    body=mail.body,
                ),
                user=request.user,
                kind=(
                    JournalEntryKind.DANGER if error_message else JournalEntryKind.INFO
                ),
            )

        return redirect(instance.get_absolute_url())
