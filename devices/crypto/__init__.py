from ..enums import PasswordAlgorithm
from .arista import AristaType7Cipher
from .base import PasswordCipher
from .cisco import CiscoType7Cipher
from .juniper import JuniperType9Cipher

__all__ = ("PasswordCipher", "get_cipher")

CIPHERS: dict[str, PasswordCipher] = {
    PasswordAlgorithm.ARISTA_TYPE7: AristaType7Cipher(),
    PasswordAlgorithm.CISCO_TYPE7: CiscoType7Cipher(),
    PasswordAlgorithm.JUNIPER_TYPE9: JuniperType9Cipher(),
}


def get_cipher(algorithm: str) -> PasswordCipher | None:
    """
    Retrieve the password cipher instance based on the specified algorithm.
    """
    return CIPHERS.get(algorithm)
