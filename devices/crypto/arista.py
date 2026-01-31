# This code is based on the Arista AVD password utilities
#
# Original credit goes to Kristian Kohntopp @isotopp
# https://blog.koehntopp.info/2021/11/22/arista-type-7-passwords.html
# https://github.com/aristanetworks/avd/blob/devel/python-avd/pyavd/_utils/password_utils/

import base64
import binascii

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
from cryptography.hazmat.primitives.ciphers import Cipher, modes

from .base import PasswordCipher

__all__ = ("AristaType7Cipher",)

SEED = b"\xd5\xa8\xc9\x1e\xf5\xd5\x8a\x23"

PARITY_BITS = [
    0x01,
    0x01,
    0x02,
    0x02,
    0x04,
    0x04,
    0x07,
    0x07,
    0x08,
    0x08,
    0x0B,
    0x0B,
    0x0D,
    0x0D,
    0x0E,
    0x0E,
    0x10,
    0x10,
    0x13,
    0x13,
    0x15,
    0x15,
    0x16,
    0x16,
    0x19,
    0x19,
    0x1A,
    0x1A,
    0x1C,
    0x1C,
    0x1F,
    0x1F,
    0x20,
    0x20,
    0x23,
    0x23,
    0x25,
    0x25,
    0x26,
    0x26,
    0x29,
    0x29,
    0x2A,
    0x2A,
    0x2C,
    0x2C,
    0x2F,
    0x2F,
    0x31,
    0x31,
    0x32,
    0x32,
    0x34,
    0x34,
    0x37,
    0x37,
    0x38,
    0x38,
    0x3B,
    0x3B,
    0x3D,
    0x3D,
    0x3E,
    0x3E,
    0x40,
    0x40,
    0x43,
    0x43,
    0x45,
    0x45,
    0x46,
    0x46,
    0x49,
    0x49,
    0x4A,
    0x4A,
    0x4C,
    0x4C,
    0x4F,
    0x4F,
    0x51,
    0x51,
    0x52,
    0x52,
    0x54,
    0x54,
    0x57,
    0x57,
    0x58,
    0x58,
    0x5B,
    0x5B,
    0x5D,
    0x5D,
    0x5E,
    0x5E,
    0x61,
    0x61,
    0x62,
    0x62,
    0x64,
    0x64,
    0x67,
    0x67,
    0x68,
    0x68,
    0x6B,
    0x6B,
    0x6D,
    0x6D,
    0x6E,
    0x6E,
    0x70,
    0x70,
    0x73,
    0x73,
    0x75,
    0x75,
    0x76,
    0x76,
    0x79,
    0x79,
    0x7A,
    0x7A,
    0x7C,
    0x7C,
    0x7F,
    0x7F,
]

ENC_SIG = b"\x4c\x88\xbb"


def _des_setparity(key: bytes | bytearray) -> bytes:
    """Set parity bits for DES key."""
    res = b""
    for b in key:
        pos = b & 0x7F
        res += PARITY_BITS[pos].to_bytes(1, byteorder="big")
    return res


def _hashkey(pw: bytes) -> bytes:
    """Hash a key for use in TripleDES encryption."""
    result = bytearray(SEED)

    for idx, b in enumerate(pw):
        result[idx & 7] ^= b

    result = _des_setparity(result)

    return bytes(result)


class AristaType7Cipher(PasswordCipher):
    """
    Arista Type 7 password encryption/decryption implementation.

    This uses TripleDES CBC encryption. Unlike Cisco Type 7, it requires a key
    derived from the peer group name or neighbor IP address.
    """

    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value appears to be Arista Type 7 encrypted.

        Note: Arista Type 7 encryption produces opaque ciphertext with no visible
        prefix. This method uses a heuristic: valid base64 of the right length
        (multiple of 4, decodes to multiple of 8 bytes for TripleDES block size).
        This is not 100% reliable but provides a reasonable check.
        """
        if not value:
            return False

        # Check if it looks like base64 encoded TripleDES output
        try:
            # Must be valid base64
            data = base64.b64decode(value)
            # TripleDES produces output in 8-byte blocks, minimum 8 bytes
            return len(data) >= 8 and len(data) % 8 == 0
        except binascii.Error:
            return False

    def decrypt(self, value: str, key: str = "") -> str:
        """
        Decrypt an Arista Type 7 encrypted password.

        The key is used for decryption, usually derived from <NEIGHBOR_IP>.
        """
        if not value:
            return ""
        if not key:
            raise ValueError("Key is required for Arista Type 7")
        if not self.is_encrypted(value):
            return value

        try:
            data = base64.b64decode(value)
        except binascii.Error:
            return value

        key_bytes = bytes(f"{key}_passwd", encoding="UTF-8")
        hashed_key = _hashkey(key_bytes)

        cipher = Cipher(TripleDES(hashed_key), modes.CBC(bytes(8)), default_backend())
        decryptor = cipher.decryptor()
        result = decryptor.update(data)
        decryptor.finalize()

        # Checking the decrypted string
        pad = result[3] >> 4
        if result[:3] != ENC_SIG or pad >= 8 or len(result[4:]) < pad:
            raise ValueError("Invalid Encrypted String")

        password_len = len(result) - pad
        return result[4:password_len].decode(encoding="UTF-8")

    def encrypt(self, value: str, key: str = "") -> str:
        """
        Encrypt a password using Arista Type 7 encryption.

        The key is used for encryption, usually derived from <NEIGHBOR_IP>.
        """
        if not value:
            return ""
        if not key:
            raise ValueError("Key is required for Arista Type 7")
        if self.is_encrypted(value=value):
            return value

        data = bytes(value, encoding="UTF-8")
        key_bytes = bytes(f"{key}_passwd", encoding="UTF-8")
        hashed_key = _hashkey(key_bytes)

        padding = (8 - ((len(data) + 4) % 8)) % 8
        ciphertext = ENC_SIG + bytes([padding * 16 + 0xE]) + data + bytes(padding)

        cipher = Cipher(TripleDES(hashed_key), modes.CBC(bytes(8)), default_backend())
        encryptor = cipher.encryptor()
        result = encryptor.update(ciphertext)
        encryptor.finalize()

        return base64.b64encode(result).decode(encoding="UTF-8")
