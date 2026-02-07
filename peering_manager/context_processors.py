from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings as django_settings

from peering.models import AutonomousSystem
from peering_manager.navigation import get_navigation
from peeringdb.sync import PeeringDB

if TYPE_CHECKING:
    from django.http import HttpRequest


def affiliated_autonomous_systems(request: HttpRequest) -> dict[str, Any]:
    if request.user.is_authenticated:
        try:
            context_as = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
        except AutonomousSystem.DoesNotExist:
            context_as = None
        return {
            "affiliated_autonomous_systems": AutonomousSystem.objects.filter(
                affiliated=True
            ),
            "context_as": context_as,
        }
    return {}


def navigation(request: HttpRequest) -> dict[str, list[dict[str, Any]]]:
    return {"navigation": get_navigation(request=request)}


def settings(request: HttpRequest) -> dict[str, Any]:
    return {
        "settings": django_settings,
        "peeringdb_last_synchronisation": PeeringDB().get_last_synchronisation(),
    }
