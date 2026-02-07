from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from django.urls import reverse

from peering.models import AutonomousSystem

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest

__all__ = ["get_navigation"]


@dataclass
class MenuItem:
    label: str
    url_name: str
    icon: str = ""
    staff_only: bool = False
    query_params: Callable[[HttpRequest], str] | None = None
    extra_active_patterns: list[str] = field(default_factory=list)


@dataclass
class MenuGroup:
    label: str
    icon: str
    menu_id: str
    items: list[MenuItem] = field(default_factory=list)
    staff_only: bool = False


def _affiliated_query_params(request: HttpRequest) -> str:
    if request.user.is_authenticated:
        with contextlib.suppress(AutonomousSystem.DoesNotExist):
            context_as = AutonomousSystem.objects.get(
                pk=request.user.preferences.get("context.as")
            )
            return f"?affiliated={context_as.pk}"
    return ""


NAVIGATION: list[MenuItem | MenuGroup] = [
    MenuItem(
        label="Autonomous Systems",
        url_name="peering:autonomoussystem_list",
        icon="fa-solid fa-building",
    ),
    MenuItem(
        label="BGP Groups",
        url_name="peering:bgpgroup_list",
        icon="fa-regular fa-object-group",
    ),
    MenuItem(
        label="Internet Exchanges",
        url_name="peering:internetexchange_list",
        icon="fa-solid fa-right-left",
    ),
    MenuGroup(
        label="Network",
        icon="fa-solid fa-network-wired",
        menu_id="net-menu",
        items=[
            MenuItem(label="Connections", url_name="net:connection_list"),
            MenuItem(label="BFD", url_name="net:bfd_list"),
        ],
    ),
    MenuGroup(
        label="Provisioning",
        icon="fa-solid fa-folder-tree",
        menu_id="provisioning-menu",
        items=[
            MenuItem(label="Available IXP Peers", url_name="peeringdb:ixp_peers"),
            MenuItem(label="Hidden Peers", url_name="peeringdb:hiddenpeer_list"),
            MenuItem(
                label="Send E-mail to Network",
                url_name="peeringdb:email_network",
                query_params=_affiliated_query_params,
            ),
        ],
    ),
    MenuGroup(
        label="Policy Options",
        icon="fa-solid fa-filter",
        menu_id="policyoptions-menu",
        items=[
            MenuItem(label="Communities", url_name="bgp:community_list"),
            MenuItem(label="Routing Policies", url_name="peering:routingpolicy_list"),
        ],
    ),
    MenuGroup(
        label="Devices",
        icon="fa-solid fa-server",
        menu_id="devices-menu",
        items=[
            MenuItem(label="Configurations", url_name="devices:configuration_list"),
            MenuItem(label="Routers", url_name="devices:router_list"),
            MenuItem(label="Platforms", url_name="devices:platform_list"),
        ],
    ),
    MenuGroup(
        label="Messaging",
        icon="fa-solid fa-message",
        menu_id="messaging-menu",
        items=[
            MenuItem(label="Contacts", url_name="messaging:contact_list"),
            MenuItem(label="Contact Roles", url_name="messaging:contactrole_list"),
            MenuItem(label="E-mails", url_name="messaging:email_list"),
        ],
    ),
    MenuGroup(
        label="3rd Party",
        icon="fa-solid fa-sliders",
        menu_id="thirdparty-menu",
        items=[
            MenuItem(label="PeeringDB", url_name="peeringdb:cache_management"),
            MenuItem(label="IX-API", url_name="extras:ixapi_list"),
        ],
    ),
    MenuGroup(
        label="Operations",
        icon="fa-solid fa-gears",
        menu_id="operations-menu",
        items=[
            MenuItem(label="Data Sources", url_name="core:datasource_list"),
            MenuItem(label="Jobs", url_name="core:job_list"),
            MenuItem(label="Webhooks", url_name="extras:webhook_list"),
            MenuItem(label="Journal Entries", url_name="extras:journalentry_list"),
            MenuItem(label="Change Log", url_name="core:objectchange_list"),
        ],
    ),
    MenuGroup(
        label="Customisation",
        icon="fa-solid fa-toolbox",
        menu_id="customisation-menu",
        items=[
            MenuItem(label="Relationships", url_name="bgp:relationship_list"),
            MenuItem(label="Config Contexts", url_name="extras:configcontext_list"),
            MenuItem(label="Export Templates", url_name="extras:exporttemplate_list"),
            MenuItem(label="Tags", url_name="extras:tag_list"),
        ],
    ),
    MenuGroup(
        label="Admin",
        icon="fa-solid fa-user-group",
        menu_id="admin-menu",
        staff_only=True,
        items=[
            MenuItem(label="System", url_name="core:system"),
            MenuItem(
                label="Background Tasks",
                url_name="core:background_queue_list",
                extra_active_patterns=[
                    "/core/background-workers/",
                    "/core/background-tasks/",
                ],
            ),
        ],
    ),
]


def _resolve_item(item: MenuItem, request: HttpRequest) -> dict[str, Any]:
    url = reverse(item.url_name)
    patterns = [url, *item.extra_active_patterns]
    is_active = any(pattern in request.path for pattern in patterns)
    if item.query_params:
        url += item.query_params(request)
    return {"label": item.label, "url": url, "is_active": is_active}


def get_navigation(request: HttpRequest) -> list[dict[str, Any]]:
    is_staff = request.user.is_staff if request.user.is_authenticated else False
    result = []

    for entry in NAVIGATION:
        if entry.staff_only and not is_staff:
            continue

        if isinstance(entry, MenuItem):
            resolved = _resolve_item(item=entry, request=request)
            resolved["type"] = "item"
            resolved["icon"] = entry.icon
            result.append(resolved)
        elif isinstance(entry, MenuGroup):
            items = []
            for item in entry.items:
                if item.staff_only and not is_staff:
                    continue
                items.append(_resolve_item(item=item, request=request))
            result.append(
                {
                    "type": "group",
                    "label": entry.label,
                    "icon": entry.icon,
                    "menu_id": entry.menu_id,
                    "items": items,
                }
            )

    return result
