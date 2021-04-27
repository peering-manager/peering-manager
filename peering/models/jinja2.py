import ipaddress

from django.db.models.query import QuerySet

from devices.crypto.cisco import MAGIC as CISCO_MAGIC
from peering.models import AutonomousSystem, InternetExchange
from peering.models.abstracts import BGPSession
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

    return 6 if ipv6(value.ip_address) else 4


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
    return password


def filter(queryset, **kwargs):
    """
    Returns a filtered queryset based on provided criteria.
    """
    if type(v) is not QuerySet:
        raise TypeError("cannot filter data not in the database")
    return queryset.filter(**kwargs)


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
    Returns the number of items in a queryset, list or dict.
    """
    if type(value) in [dict, list, tuple]:
        return len(value)

    if type(value) is QuerySet:
        return value.count()

    return 0


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


def sessions_attr(value, field, family=0):
    """
    Returns a list of values for a given field for all peering sessions.
    """
    return sessions(value, family=family).value_list(field, flat=True)


def route_server(value, field=""):
    """
    Returns a list of all route server sessions for an IXP.

    If field is set, only the field will be returned.
    """
    if type(value) is not InternetExchange:
        raise ValueError("value is not an internet exchange")

    if field:
        return sessions(value).filter(is_route_server=True).value_list(field, flat=True)
    else:
        return sessions(value).filter(is_route_server=True)


def prefix_list(value, family=0):
    """
    Returns the prefixes for the given AS.
    """
    if type(value) is not AutonomousSystem:
        raise ValueError("value is not an autonomous system")

    return value.get_irr_as_set_prefixes(family)


def tags(value):
    """
    Returns an iterable containing tags if the object as any.
    """
    if not isinstance(value, TaggableModel):
        raise AttributeError("object has not tags")
    return value.tags.all()


FILTER_DICT = {
    # IP address utilities
    "ipv4": ipv4,
    "ipv6": ipv6,
    # Length filter and synonyms
    "length": length,
    "len": length,
    "count": length,
    # Filtering
    "filter": filter,
    # BGP sessions
    "sessions": sessions,
    "sessions_attr": sessions_attr,
    "route_server": route_server,
    "ip_version": ip_version,
    "max_prefix": max_prefix,
    # Routing policies
    "iter_export_policies": iter_export_policies,
    "iter_import_policies": iter_import_policies,
    "merge_export_policies": merge_export_policies,
    "merge_import_policies": merge_import_policies,
    "prefix_list": prefix_list,
    "tags": tags,
    "cisco_password": cisco_password,
}

__all__ = ["FILTER_DICT"]
