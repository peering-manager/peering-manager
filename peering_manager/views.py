import platform
import sys

from django.conf import settings
from django.shortcuts import render
from django.views.generic import View
from packaging import version

from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    Configuration,
    DirectPeeringSession,
    Email,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peeringdb.models import Synchronization
from utils.models import ObjectChange

from .releases import get_latest_release


def handle_500(request):
    """
    Custom 500 error handler.
    """
    type, error, traceback = sys.exc_info()
    del traceback
    return render(
        request,
        "500.html",
        {
            "python_version": platform.python_version(),
            "peering_manager_version": settings.VERSION,
            "exception": str(type),
            "error": error,
        },
        status=500,
    )


def trigger_500(request):
    """
    Method to fake trigger a server error for test reporting.
    """
    raise Exception("Manually triggered error.")


class Home(View):
    def get(self, request):
        statistics = {
            "autonomous_systems_count": AutonomousSystem.objects.count(),
            "bgp_groups_count": BGPGroup.objects.count(),
            "communities_count": Community.objects.count(),
            "configurations_count": Configuration.objects.count(),
            "direct_peering_sessions_count": DirectPeeringSession.objects.count(),
            "emails_count": Email.objects.count(),
            "internet_exchanges_count": InternetExchange.objects.count(),
            "internet_exchange_peering_sessions_count": InternetExchangePeeringSession.objects.count(),
            "routers_count": Router.objects.count(),
            "routing_policies_count": RoutingPolicy.objects.count(),
        }

        # Check whether a new release is available for staff and superuser
        new_release = None
        if request.user.is_staff or request.user.is_superuser:
            latest_release, release_url = get_latest_release()
            if isinstance(latest_release, version.Version):
                current_version = version.parse(settings.VERSION)
                if latest_release > current_version:
                    new_release = {"version": str(latest_release), "url": release_url}

        context = {
            "statistics": statistics,
            "changelog": ObjectChange.objects.select_related(
                "user", "changed_object_type"
            )[:15],
            "synchronizations": Synchronization.objects.all()[:5],
            "new_release": new_release,
        }
        return render(request, "home.html", context)
