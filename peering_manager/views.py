import sys

from django.shortcuts import render
from django.views.generic import View

from peering.models import (
    AutonomousSystem,
    Community,
    ConfigurationTemplate,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from peeringdb.models import Synchronization
from utils.models import ObjectChange


def handle_500(request):
    """
    Custom 500 error handler.
    """
    type, error, traceback = sys.exc_info()
    del traceback
    return render(
        request, "500.html", {"exception": str(type), "error": error}, status=500
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
            "internet_exchanges_count": InternetExchange.objects.count(),
            "communities_count": Community.objects.count(),
            "templates_count": ConfigurationTemplate.objects.count(),
            "routers_count": Router.objects.count(),
            "direct_peering_sessions_count": DirectPeeringSession.objects.count(),
            "internet_exchange_peering_sessions_count": InternetExchangePeeringSession.objects.count(),
            "routing_policies_count": RoutingPolicy.objects.count(),
        }
        context = {
            "statistics": statistics,
            "changelog": ObjectChange.objects.select_related(
                "user", "changed_object_type"
            )[:50],
            "synchronizations": Synchronization.objects.all()[:5],
        }
        return render(request, "home.html", context)
