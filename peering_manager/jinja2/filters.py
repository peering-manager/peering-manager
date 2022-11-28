import ipaddress
import json
import unicodedata

import yaml
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet

from devices.crypto.cisco import MAGIC as CISCO_MAGIC
from net.enums import ConnectionStatus
from net.models import Connection
from peering.enums import BGPGroupStatus, BGPSessionStatus, DeviceStatus, IPFamily
from peering.models.abstracts import BGPSession
from peering.models.models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
)
from utils.functions import get_key_in_hash, serialize_object
from utils.models import ConfigContextMixin, TagsMixin


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


def ip(value):
    """
    Returns the IP address without prefix length.
    """
    if isinstance(value, BGPSession):
        address = value.ip_address
    elif type(value) in (
        ipaddress.IPv4Interface,
        ipaddress.IPv6Interface,
        ipaddress.IPv4Address,
        ipaddress.IPv6Address,
    ):
        address = value
    else:
        try:
            address = ipaddress.ip_interface(value)
        except ValueError:
            address = ipaddress.ip_address(value)

    if type(address) in (ipaddress.IPv4Interface, ipaddress.IPv6Interface):
        return str(address.ip)
    elif type(address) in (ipaddress.IPv4Address, ipaddress.IPv6Address):
        return str(address)
    else:
        return address


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


def inherited_status(value):
    """
    Returns the status of an object taking into account the status of its parent.

    If the status of the object is equivalent to a disabled one, the status of the
    parent will not be resolved as this kind of status is considered more specific.

    In case of connections, both IXP's and router's statuses will be checked (IXP's
    first).

    In case of direct peering sessions, both group's and router's statuses will be
    checked (group's first).

    In case of IXP peering sessions, connection's status will be checked but that will
    trigger a recursive check for it which means it'll take into account the IXP or
    router status.
    """
    if not hasattr(value, "status"):
        raise ValueError("value has no status property")

    if type(value) is Connection and value.status != ConnectionStatus.DISABLED:
        # Disabled on IXP probably means the same for connections
        if value.internet_exchange_point.status == BGPGroupStatus.DISABLED:
            return ConnectionStatus.DISABLED
        # Maintenance on IXP probably means the same for connections
        if value.internet_exchange_point.status == BGPGroupStatus.MAINTENANCE:
            return ConnectionStatus.MAINTENANCE
        # Maintenance on a router probably means the same for connections
        if value.router and value.router.status == DeviceStatus.MAINTENANCE:
            return ConnectionStatus.MAINTENANCE

    if (
        type(value) is DirectPeeringSession
        and value.status != BGPSessionStatus.DISABLED
    ):
        if value.bgp_group:
            # Disabled group probably means sessions should be teared down
            if value.bgp_group.status == BGPGroupStatus.DISABLED:
                return BGPSessionStatus.DISABLED
            # Maintenance group probably means sessions should be less preferred
            if value.bgp_group.status == BGPGroupStatus.MAINTENANCE:
                return BGPSessionStatus.MAINTENANCE
        # Maintenance on a router probably means sessions should be less preferred
        if value.router and value.router.status == DeviceStatus.MAINTENANCE:
            return BGPSessionStatus.MAINTENANCE

    if (
        type(value) is InternetExchangePeeringSession
        and value.status != BGPSessionStatus.DISABLED
    ):
        # Disabled connection probably means sessions should be teared down
        if inherited_status(value.ixp_connection) == ConnectionStatus.DISABLED:
            return BGPSessionStatus.DISABLED
        # Maintenance connection probably means sessions should be less preferred
        if inherited_status(value.ixp_connection) == ConnectionStatus.MAINTENANCE:
            return BGPSessionStatus.MAINTENANCE

    return value.status


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
                valid = getattr(i, k) == v
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


def unique(value, field):
    """
    Returns an iterable containing unique items based on a field (and its value).
    """
    if type(value) is QuerySet:
        return value.order_by().distinct(field)

    try:
        iter(value)
    except TypeError:
        raise ValueError("value cannot be filtered (not iterable)")

    unique_items = []
    seen_values = []

    # Build a list with unique items matching one field value
    # Fail validation of an item if it does not have the attribute
    for i in value:
        try:
            value = getattr(i, field)
            if value not in seen_values:
                seen_values.append(value)
                unique_items.append(i)
        except AttributeError:
            continue

    return unique_items


def iterate(value, field):
    """
    Yields the value of a given field of an item in an iteratable.

    If the item does not have the field, it will simply yield a null value.
    """
    for item in value:
        yield getattr(item, field, None)


def iter_export_policies(value, field="", family=-1):
    """
    Returns a list of policies to apply on export.

    An optional field can be passed as parameter to return only this field's value.
    An optional family can be passed to return only policies matching the address
    family.
    """
    if not hasattr(value, "export_policies"):
        raise AttributeError("{value} has not export policies")

    if type(field) is not str:
        raise AttributeError(f"field must be a string'")

    policies = value.export_policies()
    if family in IPFamily.values():
        policies = filter(policies, address_family__in=[0, family])

    if field:
        return [getattr(p, field) for p in policies]

    return list(policies)


def iter_import_policies(value, field="", family=-1):
    """
    Returns a list of policies to apply on import.

    An optional field can be passed as parameter to return only this field's value.
    An optional family can be passed to return only policies matching the address
    family.
    """
    if not hasattr(value, "import_policies"):
        raise AttributeError("{value} has not import policies")

    if type(field) is not str:
        raise AttributeError(f"field must be a string'")

    policies = value.import_policies()
    if family in IPFamily.values():
        policies = filter(policies, address_family__in=[0, family])

    if field:
        return [getattr(p, field) for p in policies]

    return list(policies)


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
    """
    Returns connections attached to an object.
    """
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
    Returns the prefixes for the given AS or IXP.
    """
    if type(value) is AutonomousSystem:
        return value.get_irr_as_set_prefixes(family=family)

    if type(value) is InternetExchange:
        if family in (4, 6):
            return value.peeringdb_prefixes.get(f"ipv{family}", [])
        else:
            return value.peeringdb_prefixes

    raise ValueError("value has no prefixes")


def safe_string(value):
    """
    Returns a safe string (retaining only ASCII characters).
    """
    return unicodedata.normalize("NFKD", value).encode("ASCII", "ignore").decode()


def tags(value):
    """
    Returns an iterable containing tags associated with an object."
    """
    if not isinstance(value, TagsMixin):
        raise AttributeError("object has no tags")
    return value.tags.all()


def has_tag(value, tag):
    """
    Returns a boolean indicating if an objects has the given tag.
    """
    if not isinstance(value, TagsMixin):
        raise AttributeError("object has no tags")

    return value.tags.filter(Q(name=tag) | Q(slug=tag)).count() > 0


def has_not_tag(value, tag):
    """
    Returns a boolean indicating if an objects has the given tag.
    """
    if not isinstance(value, TagsMixin):
        raise AttributeError("object has no tags")

    return value.tags.filter(Q(name=tag) | Q(slug=tag)).count() == 0


def context_has_key(value, key, recursive=True):
    """
    Returns whether or not a config context has a key.

    The `recursive` parameter can be set to `False` to avoid looking in nested hashes.
    """
    if not isinstance(value, ConfigContextMixin):
        raise AttributeError("object has no config context")

    _, found = get_key_in_hash(value.get_config_context(), key, recursive=recursive)
    return found


def context_has_not_key(value, key, recursive=True):
    """
    Returns whether or not a config context has **not** a key.

    The `recursive` parameter can be set to `False` to avoid looking in nested hashes.
    """
    return not context_has_key(value, key, recursive=recursive)


def context_get_key(value, key, default=None, recursive=True):
    """
    Returns the value of a key in a config context.

    The `default` parameter can be set to any value if the key is not to be found.

    The `recursive` parameter can be set to `False` to avoid looking in nested hashes.
    """
    if not isinstance(value, ConfigContextMixin):
        raise AttributeError("object has no config context")

    value, _ = get_key_in_hash(
        value.get_config_context(), key, default=default, recursive=recursive
    )
    return value


def _serialize(value):
    """
    Serializes a queryset, an object or a basic value as something usable by a JSON or
    YAML dumper.
    """
    if type(value) is QuerySet:
        data = [serialize_object(i) for i in value]
    elif isinstance(value, models.Model):
        data = serialize_object(value)
    else:
        data = value
    return data


def as_json(value, indent=4, sort_keys=True):
    """
    Render something as JSON.
    """
    return json.dumps(_serialize(value), indent=indent, sort_keys=sort_keys)


def as_yaml(value, indent=2, sort_keys=True):
    """
    Render something as YAML.
    """
    return yaml.dump(
        _serialize(value), indent=indent, sort_keys=sort_keys, default_flow_style=False
    )


def indent(value, n, chars=" ", reset=False):
    """
    Appends `n` chars to the beginning of each line of a value which is parsed as a
    string. Remove the chars before applying the indentation if `reset` is set to
    `True`.
    """
    r = ""

    for line in str(value).splitlines(True):
        r += f"{chars * n}{line if not reset else line.lstrip(chars)}"

    return r


FILTER_DICT = {
    # Generics
    "safe_string": safe_string,
    "tags": tags,
    "has_tag": has_tag,
    "has_not_tag": has_not_tag,
    "inherited_status": inherited_status,
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
    "unique": unique,
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
    "ip": ip,
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
    # Config contexts
    "context_has_key": context_has_key,
    "context_has_not_key": context_has_not_key,
    "context_get_key": context_get_key,
    # Formatting
    "as_json": as_json,
    "as_yaml": as_yaml,
    "indent": indent,
}

__all__ = ("FILTER_DICT",)
