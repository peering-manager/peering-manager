from devices.crypto.cisco import MAGIC as CISCO_MAGIC
from peering.models import AutonomousSystem


def cisco_password(password):
    """
    Returns a Cisco type 7 password without the magic word.
    """
    if password.startswith(CISCO_MAGIC):
        return password[2:]
    return password


def prefix_list(asn, address_family=0):
    """
    Returns the prefixes for the given AS.
    """
    if not asn:
        return []
    autonomous_system = AutonomousSystem.objects.get(asn=asn)
    return autonomous_system.get_irr_as_set_prefixes(address_family)


FILTER_DICT = {"cisco_password": cisco_password, "prefix_list": prefix_list}

__all__ = ["FILTER_DICT"]
