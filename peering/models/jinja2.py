import ipaddress
import unicodedata

from django.db.models import Q
from django.db.models.query import QuerySet

from devices.crypto.cisco import MAGIC as CISCO_MAGIC
from net.models import Connection
from peering.models.abstracts import BGPSession
from peering.models.models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
)
from utils.models import TaggableModel


def ipv4(value):
    """
    Parses the value as an IPv4 address and returns it.
    """
    try:
        return ipaddress.IPv4Address(value)
    except ValueError:
        pass

    try:
        return ipaddress.IPv4Interface(value)
    except ValueError:
        pass

    return None


def ipv6(value):
    """
    Parses the value as an IPv6 address and returns it.
    """
    try:
        return ipaddress.IPv6Address(value)
    except ValueError:
        pass

    try:
        return ipaddress.IPv6Interface(value)
    except ValueError:
        pass

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


def filter(value, **kwargs):
    """
    Returns a filtered queryset or iterable based on provided criteria.
    """
    if type(value) is QuerySet:
        return value.filter(**kwargs)

    try:
        iter(value)
    except TypeError:
        raise ValueError("value cannot be filtered (not iterable)")

    # Build a list with items matching all provided criteria
    # Fail validation of an item if it does not have one of the attributes
    filtered = []
    for i in value:
        valid = True
        for k, v in kwargs.items():
            try:
                valid = getattr(i, k, None) != v
            except AttributeError:
                valid = False

            if not valid:
                break

        if valid:
            filtered.append(i)

    return filtered


def get(queryset, **kwargs):
    """
    Returns a single object from a queryset and a filter. If more than one object
    matches the filterm a queryset will be return.
    """
    q = filter(queryset, **kwargs)

    if q.count() == 1:
        return q.get()
    else:
        return q


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


def communities(value, field=""):
    """
    Returns a list of communities applied to an AS, a group, an IXP or a session.
    """
    c = None

    if type(value) is InternetExchangePeeringSession:
        c = value.ixp_connection.internet_exchange_point.communities
    if type(value) is DirectPeeringSession:
        c = value.bgp_group.communities
    if hasattr(value, "communities"):
        c = value.communities

    if c:
        if field:
            return [getattr(i, field) for i in c]
        return c.all()

    return []


def merge_communities(value):
    """
    Merges and returns communities.
    """
    if not hasattr(value, "merged_communities"):
        raise AttributeError("{value} has not merged communities")

    return value.merged_communities()


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


def connections(value):
    if not hasattr(value, "get_connections"):
        raise AttributeError(f"{value} has no connections")
    return value.get_connections()


def local_ips(value, family=0):
    """
    Returns local IP addresses for a BGP session or an IXP.
    """
    if isinstance(value, DirectPeeringSession):
        return value.local_ip_address

    if isinstance(value, InternetExchangePeeringSession):
        if value.ip_address.version == 6:
            return value.ixp_connection.ipv6_address
        else:
            return value.ixp_connection.ipv4_address

    if isinstance(value, InternetExchange):
        ips = []
        for c in Connection.objects.filter(internet_exchange_point=value):
            if c.ipv4_address and family != 6:
                ips.append(c.ipv4_address)
            if c.ipv6_address and family != 4:
                ips.append(c.ipv6_address)
        return ips

    return None


def direct_sessions(value, family=0, group=None):
    """
    Returns a queryset of direct peering sessions.

    If family is set to 4 or 6, only the sessions matching the IP address
    family will be returned. If family is not set all sessions matching all address
    families will be returned.
    """
    if not hasattr(value, "get_direct_peering_sessions"):
        raise AttributeError(f"{value} has no direct peering sessions, try `sessions`")

    s = value.get_direct_peering_sessions(bgp_group=group)

    if family not in (4, 6):
        return s
    else:
        return s.filter(ip_address__family=family)


def ixp_sessions(value, family=0, ixp=None):
    """
    Returns a queryset of IXP peering sessions.

    If family is set to 4 or 6, only the sessions matching the IP address
    family will be returned. If family is not set all sessions matching all address
    families will be returned.

    If ixp is set, only sessions for the given IXP will be returned. If ixp is not set
    all IXP sessions will be returned.
    """
    if not hasattr(value, "get_ixp_peering_sessions"):
        raise AttributeError(f"{value} has no ixp peering sessions, try `sessions`")

    s = value.get_ixp_peering_sessions(internet_exchange_point=ixp)

    if family not in (4, 6):
        return s
    else:
        return s.filter(ip_address__family=family)


def sessions(value, family=0):
    """
    Returns a queryset of peering sessions, they can be direct or IXP but not both.

    If family is set to 4 or 6, only the sessions matching the IP address family will
    be returned. If family is not set all sessions matching all address families will
    be returned.
    """
    if not hasattr(value, "get_peering_sessions"):
        raise AttributeError(
            f"{value} has no generic peering sessions, try `direct_sessions` or `ixp_sessions`"
        )

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


def missing_sessions(value, other, ixp=None):
    """
    Returns all missing sessions between two ASNs, optionally on an IXP.
    """
    return value.get_missing_peering_sessions(other, internet_exchange_point=ixp)


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
        raise AttributeError("object has no tags")
    return value.tags.all()


def has_tag(value, tag):
    """
    Returns a boolean indicating if an objects has the given tag.
    """
    if not isinstance(value, TaggableModel):
        raise AttributeError("object has no tags")

    return value.tags.filter(Q(name=tag) | Q(slug=tag)).count() > 0


def has_not_tag(value, tag):
    """
    Returns a boolean indicating if an objects has the given tag.
    """
    if not isinstance(value, TaggableModel):
        raise AttributeError("object has no tags")

    return value.tags.filter(Q(name=tag) | Q(slug=tag)).count() == 0


FILTER_DICT = {
    # Generics
    "safe_string": safe_string,
    "tags": tags,
    "has_tag": has_tag,
    "has_not_tag": has_not_tag,
    # IP address utilities
    "ipv4": ipv4,
    "ipv6": ipv6,
    # Length filter and synonyms
    "length": length,
    "len": length,
    "count": length,
    # Filtering
    "filter": filter,
    "get": get,
    "iterate": iterate,
    # Autonomous system
    "ixps": ixps,
    "shared_ixps": shared_ixps,
    "missing_sessions": missing_sessions,
    "prefix_list": prefix_list,
    "direct_sessions": direct_sessions,
    # BGP groups
    "local_ips": local_ips,
    # BGP sessions
    "direct_sessions": direct_sessions,
    "ixp_sessions": ixp_sessions,
    "sessions": sessions,
    "route_server": route_server,
    "ip_version": ip_version,
    "max_prefix": max_prefix,
    "cisco_password": cisco_password,
    # Connections
    "connections": connections,
    # Routers
    "direct_peers": direct_peers,
    "ixp_peers": ixp_peers,
    # Communities
    "communities": communities,
    "merge_communities": merge_communities,
    # Routing policies
    "iter_export_policies": iter_export_policies,
    "iter_import_policies": iter_import_policies,
    "merge_export_policies": merge_export_policies,
    "merge_import_policies": merge_import_policies,
}

__all__ = ["FILTER_DICT"]
