from devices.crypto.cisco import MAGIC as CISCO_MAGIC
from peering.models import AutonomousSystem
from utils.models import TaggableModel


def cisco_password(password):
    """
    Returns a Cisco type 7 password without the magic word.
    """
    if password.startswith(CISCO_MAGIC):
        return password[2:]
    return password


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


def iter_sessions(value):
    """
    Yields a session and its address family at each call.
    """
    for session in value.get_peering_sessions():
        yield session.ip_address.version, session


def iter_all_sessions(value):
    """
    Yields a session, its group and its address family at each call.
    """
    try:
        iter(value)

        for group in value:
            for session in group.get_peering_sessions():
                yield group, session.ip_address.version, session
    except TypeError:
        pass


def prefix_list(asn, address_family=0):
    """
    Returns the prefixes for the given AS.
    """
    try:
        int(asn)
        autonomous_system = AutonomousSystem.objects.get(asn=asn)
        return autonomous_system.get_irr_as_set_prefixes(address_family)
    except ValueError:
        raise ValueError("value must be an autonomous system number")


def tags(obj):
    if not isinstance(obj, TaggableModel):
        raise AttributeError("object has not tags")
    return obj.tags.all()


FILTER_DICT = {
    "cisco_password": cisco_password,
    "iter_export_policies": iter_export_policies,
    "iter_import_policies": iter_import_policies,
    "iter_sessions": iter_sessions,
    "iter_all_sessions": iter_all_sessions,
    "prefix_list": prefix_list,
    "tags": tags,
}

__all__ = ["FILTER_DICT"]
