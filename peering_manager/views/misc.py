from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View
from packaging import version

from bgp.models import Community
from core.models import ObjectChange
from devices.models import Configuration, Router
from messaging.models import Contact, Email
from net.models import BFD, Connection
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from peering_manager.constants import SEARCH_MAX_RESULTS, SEARCH_TYPES
from peering_manager.forms import SearchForm
from peeringdb.models import Synchronisation

__all__ = ("HomeView", "SearchView")


class HomeView(View):
    def get(self, request):
        statistics = {
            "autonomous_systems_count": AutonomousSystem.objects.count(),
            "bfd_count": BFD.objects.count(),
            "bgp_groups_count": BGPGroup.objects.count(),
            "communities_count": Community.objects.count(),
            "connections_count": Connection.objects.count(),
            "direct_peering_sessions_count": DirectPeeringSession.objects.count(),
            "internet_exchanges_count": InternetExchange.objects.count(),
            "internet_exchange_peering_sessions_count": InternetExchangePeeringSession.objects.count(),
            "routers_count": Router.objects.count(),
            "routing_policies_count": RoutingPolicy.objects.count(),
            "configurations_count": Configuration.objects.count(),
            "contacts_count": Contact.objects.count(),
            "emails_count": Email.objects.count(),
        }

        # Check whether a new release is available (staff and superusers only)
        new_release = None
        if request.user.is_staff or request.user.is_superuser:
            latest_release = cache.get("latest_release")
            if latest_release:
                release_version, release_url = latest_release
                if release_version > version.parse(settings.VERSION):
                    new_release = {"version": str(release_version), "url": release_url}

        context = {
            "statistics": statistics,
            "changelog": ObjectChange.objects.select_related(
                "user", "changed_object_type"
            )[:15],
            "synchronisations": Synchronisation.objects.all()[:5],
            "new_release": new_release,
        }
        return render(request, "home.html", context)


class SearchView(View):
    def get(self, request):
        form = SearchForm(request.GET)
        results = []

        if form.is_valid():
            for obj_type in SEARCH_TYPES:
                queryset = SEARCH_TYPES[obj_type]["queryset"]
                filterset = SEARCH_TYPES[obj_type]["filterset"]
                table = SEARCH_TYPES[obj_type]["table"]
                url = SEARCH_TYPES[obj_type]["url"]

                # Construct the results table for this object type
                filtered_queryset = filterset(
                    {"q": form.cleaned_data["q"]}, queryset=queryset
                ).qs
                table = table(filtered_queryset, orderable=False, no_actions=True)
                table.paginate(per_page=SEARCH_MAX_RESULTS)

                if table.page:
                    results.append(
                        {
                            "name": queryset.model._meta.verbose_name_plural,
                            "table": table,
                            "url": f"{reverse(url)}?q={form.cleaned_data.get('q')}",
                        }
                    )

        return render(request, "search.html", {"form": form, "results": results})
