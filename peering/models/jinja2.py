import ipaddress
import unicodedata

from django.db.models.query import QuerySet

from devices.crypto.cisco import MAGIC as CISCO_MAGIC
from peering.models.abstracts import BGPSession
from peering.models.models import AutonomousSystem, BGPGroup, InternetExchange, Router
from utils.models import TaggableModel


def ipv4(value):
    """
    Parses the value as an IPv4 address and returns it.
    """
    try:
        return ipaddress.IPv4Address(value)
    except ValueError:
        return None


def ipv6(value):
    """
    Parses the value as an IPv6 address and returns it.
    """
    try:
        return ipaddress.IPv6Address(value)
    except ValueError:
        return None


def ip_version(value):
    """
    Returns the IP version of a BGP session.
    """
    if not isinstance(value, BGPSession):
        raise ValueError("value is not a bgp session")

    if ipv6(value.ip_address):
        return 6
    if ipv4(value.ip_address):
        return 4

    raise ValueError("ip address for session is invalid")


def max_prefix(value):
    """
    Returns the max prefix value for a BGP session.
    """
    if not isinstance(value, BGPSession):
        raise ValueError("value is not a bgp session")

    if ipv6(value.ip_address):
        return value.autonomous_system.ipv6_max_prefixes
    else:
        return value.autonomous_system.ipv4_max_prefixes


def cisco_password(password):
    """
    Returns a Cisco type 7 password without the magic word.
    """
    if password.startswith(CISCO_MAGIC):
        return password[2:]
    else:
        return password


def filter(queryset, **kwargs):
    """
    Returns a filtered queryset based on provided criteria.
    """
    if type(queryset) is not QuerySet:
        raise TypeError("cannot filter data not in the database")
    return queryset.filter(**kwargs)


def iterate(value, field):
    """
    Yields the value of a given field of an item in an iteratable.

    If the item does not have the field, it will simply yield a null value.
    """
    for item in value:
        yield getattr(item, field, None)


def iter_export_policies(value, field=""):
    """
    Returns a list of policies to apply on export.
    """
    if not hasattr(value, "export_policies"):
        raise AttributeError("{value} has not export policies")

    if type(field) is not str:
        raise AttributeError(f"field must be a string'")

    if field:
        return [getattr(rp, field) for rp in value.export_policies()]

    return list(value.export_policies())


def iter_import_policies(value, field=""):
    """
    Returns a list of policies to apply on import.
    """
    if not hasattr(value, "import_policies"):
        raise AttributeError("{value} has not import policies")

    if type(field) is not str:
        raise AttributeError(f"field must be a string'")

    if field:
        return [getattr(rp, field) for rp in value.import_policies()]

    return list(value.import_policies())


def length(value):
    """
    Returns the number of items in a queryset or an iterable.
    """
    if type(value) is QuerySet:
        return value.count()

    # Fallback to python's len()
    return len(value)


def merge_export_policies(value, order=""):
    """
    Merges and returns policy list for export.

    If duplicates are found, only the most specific one will be kept.
    """
    if not hasattr(value, "merged_export_policies"):
        raise AttributeError("{value} has not merged export policies")

    return value.merged_export_policies(order == "reverse")


def merge_import_policies(value, order=""):
    """
    Merges and returns policy list for import.

    If duplicates are found, only the most specific one will be kept.
    """
    if not hasattr(value, "merged_import_policies"):
        raise AttributeError("{value} has not merged import policies")

    return value.merged_import_policies(order == "reverse")


def direct_sessions(value, family=0):
    """
    Returns a queryset of direct peering sessions.

    If family is set to 4 or 6, only the sessions matching the IP address
    family will be returned. If family is not set all sessions matching all
    address families will be returned.
    """
    if not hasattr(value, "get_direct_peering_sessions"):
        raise AttributeError(f"{value} has no direct peering sessions")

    if family not in (4, 6):
        return value.get_direct_peering_sessions()
    else:
        return value.get_direct_peering_sessions().filter(ip_address__family=family)


def ixp_sessions(value, family=0):
    """
    Returns a queryset of IXP peering sessions.

    If family is set to 4 or 6, only the sessions matching the IP address
    family will be returned. If family is not set all sessions matching all
    address families will be returned.
    """
    if not hasattr(value, "get_ixp_peering_sessions"):
        raise AttributeError(f"{value} has no direct peering sessions")

    if family not in (4, 6):
        return value.get_ixp_peering_sessions()
    else:
        return value.get_ixp_peering_sessions().filter(ip_address__family=family)


def sessions(value, family=0):
    """
    Returns a queryset of peering sessions.

    If family is set to 4 or 6, only the sessions matching the IP address
    family will be returned. If family is not set all sessions matching all
    address families will be returned.
    """
    if not hasattr(value, "get_peering_sessions"):
        raise AttributeError(f"{value} has no peering sessions")

    if family not in (4, 6):
        return value.get_peering_sessions()
    else:
        return value.get_peering_sessions().filter(ip_address__family=family)


def route_server(value, family=0):
    """
    Returns a queryset listing all route server sessions for an IXP.
    """
    if type(value) is not InternetExchange:
        raise ValueError("value is not an internet exchange")

    return sessions(value, family=family).filter(is_route_server=True)


def direct_peers(value, group=""):
    """
    Returns a queryset of all autonomous systems peering directly with a router.

    An optional group can be used for filtering, always as a slug.
    """
    if type(value) is not Router:
        raise ValueError("value is not a router")

    g = None
    if group:
        try:
            g = BGPGroup.objects.get(slug=group)
        except BGPGroup.DoesNotExist:
            pass

    return value.get_direct_autonomous_systems(bgp_group=g)


def ixp_peers(value, ixp=""):
    """
    Returns a queryset of all autonomous systems peering over IXPs with a router.
    """
    if type(value) is not Router:
        raise ValueError("value is not a router")

    i = None
    if ixp:
        try:
            i = InternetExchange.objects.get(slug=ixp)
        except InternetExchange.DoesNotExist:
            pass

    return value.get_ixp_autonomous_systems(internet_exchange_point=i)


def ixps(value, other):
    """
    Returns all IXPs on which both AS are peering together.
    """
    return value.get_internet_exchange_points(other)


def shared_ixps(value, other):
    """
    Returns shared IXPs where both ASNs are present without a bilateral session.
    """
    return value.get_shared_internet_exchange_points(other)


def prefix_list(value, family=0):
    """
    Returns the prefixes for the given AS.
    """
    if type(value) is not AutonomousSystem:
        raise ValueError("value is not an autonomous system")

    return value.get_irr_as_set_prefixes(family)


def safe_string(value):
    """
    Returns a safe string (retaining only ASCII characters).
    """
    return unicodedata.normalize("NFKD", value).encode("ASCII", "ignore").decode()


def tags(value):
    """
    Returns an iterable containing tags associated with an object."
    """
    if not isinstance(value, TaggableModel):
        raise AttributeError("object has not tags")
    return value.tags.all()


FILTER_DICT = {
    # Generics
    "safe_string": safe_string,
    "tags": tags,
    # IP address utilities
    "ipv4": ipv4,
    "ipv6": ipv6,
    # Length filter and synonyms
    "length": length,
    "len": length,
    "count": length,
    # Filtering
    "filter": filter,
    "iterate": iterate,
    # Autonomous system
    "ixps": ixps,
    "shared_ixps": shared_ixps,
    "prefix_list": prefix_list,
    "direct_sessions": direct_sessions,
    "ixp_sessions": ixp_sessions,
    # BGP sessions
    "sessions": sessions,
    "route_server": route_server,
    "ip_version": ip_version,
    "max_prefix": max_prefix,
    "cisco_password": cisco_password,
    # Routers
    "direct_peers": direct_peers,
    "ixp_peers": ixp_peers,
    # Routing policies
    "iter_export_policies": iter_export_policies,
    "iter_import_policies": iter_import_policies,
    "merge_export_policies": merge_export_policies,
    "merge_import_policies": merge_import_policies,
}

__all__ = ["FILTER_DICT"]
