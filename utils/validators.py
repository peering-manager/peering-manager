import re

from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible

__all__ = ("AddressFamilyValidator", "MACAddressValidator")


@deconstructible
class AddressFamilyValidator(BaseValidator):
    compare = lambda self, value, version: value.version != version  # noqa: E731
    message = "Enter a valid IPv%(limit_value)s address."
    code = "address_version"


@deconstructible
class MACAddressValidator(BaseValidator):
    # Match MAC addresses with 12 hex digits with either `:`, `-`, `.` or nothing as
    # separator or EUI-64 formatted ones (usually used by Cisco devices)
    compare = lambda self, value: re.match(  # noqa: E731
        r"[0-9a-f]{2}([-:.]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", value.lower()
    ) or re.match(r"([0-9a-f]{4}\.){2}[0-9a-f]{4}$", value.lower())
    message = "Enter a valid Ethernet MAC address."
    code = "address_value"
