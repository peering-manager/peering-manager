# This code is the result of the attempt at converting a Perl module, the expected
# result might not actually be what we really want it to be ¯\_(ツ)_/¯
#
# https://metacpan.org/pod/Crypt::Juniper

import hashlib
import random

from .base import PasswordCipher

__all__ = ("JuniperType9Cipher",)

MAGIC = "$9$"

FAMILY = [
    "QzF3n6/9CAtpu0O",
    "B1IREhcSyrleKvMW8LXx",
    "7N-dVbwsY2g4oaJZGUDj",
    "iHkq.mPf5T",
]
EXTRA = {}
for counter, value in enumerate(FAMILY):
    for character in value:
        EXTRA[character] = 3 - counter

NUM_ALPHA = list("".join(FAMILY))
ALPHA_NUM = {NUM_ALPHA[x]: x for x in range(len(NUM_ALPHA))}

ENCODING = [
    [1, 4, 32],
    [1, 16, 32],
    [1, 8, 32],
    [1, 64],
    [1, 32],
    [1, 4, 16, 128],
    [1, 32, 64],
]


def _nibble(cref: str, length: int) -> tuple[str, str]:
    nib = cref[0:length]
    rest = cref[length:]

    if len(nib) != length:
        raise Exception(f"Ran out of characters: hit '{nib}', expecting {length} chars")

    return nib, rest


def _gap(c1: str, c2: str) -> int:
    return (ALPHA_NUM[str(c2)] - ALPHA_NUM[str(c1)]) % (len(NUM_ALPHA)) - 1


def _gap_decode(gaps: list[int], dec: list[int]) -> str:
    num = 0

    if len(gaps) != len(dec):
        raise Exception("Nibble and decode size not the same.")

    for x in range(len(gaps)):
        num += gaps[x] * dec[x]

    return chr(num % 256)


def _reverse(current: list[int]) -> list[int]:
    reversed_list = list(current)
    reversed_list.reverse()
    return reversed_list


def _gap_encode(pc: str, prev: str, encode: list[int]) -> str:
    __ord = ord(pc)

    crypt = ""
    gaps: list[int] = []
    for mod in _reverse(encode):
        gaps.insert(0, int(__ord / mod))
        __ord %= mod

    for g in gaps:
        gap = g + ALPHA_NUM[prev] + 1
        prev = NUM_ALPHA[gap % len(NUM_ALPHA)]
        crypt += prev

    return crypt


def _randc(counter: int = 0) -> str:
    return_value = ""
    for _ in range(counter):
        return_value += NUM_ALPHA[random.randrange(len(NUM_ALPHA))]
    return return_value


class JuniperType9Cipher(PasswordCipher):
    """
    Juniper Type 9 password encryption/decryption implementation.

    This is a reversible obfuscation scheme used in Juniper Junos devices.
    The key parameter is not used for this algorithm.
    """

    def is_encrypted(self, value: str) -> bool:
        """Check if a value is Juniper Type 9 encrypted."""
        if not value:
            return False
        return value.startswith(MAGIC)

    def decrypt(self, value: str, key: str = "") -> str:
        """
        Decrypt a Juniper Type 9 encrypted password.
        """
        if not value:
            return ""
        if not self.is_encrypted(value):
            return value

        chars = value.split(MAGIC, 1)[1]
        first, chars = _nibble(chars, 1)
        _, chars = _nibble(chars, EXTRA[first])
        previous = first
        decrypted = ""

        while chars:
            decode = ENCODING[len(decrypted) % len(ENCODING)]
            nibble, chars = _nibble(chars, len(decode))
            gaps = []
            for i in nibble:
                g = _gap(previous, i)
                previous = i
                gaps += [g]
            decrypted += _gap_decode(gaps, decode)

        return decrypted

    def encrypt(self, value: str, key: str = "") -> str:
        """
        Encrypt a password using Juniper Type 9.

        The optional key can be used to derive deterministic salt and rand values,
        ensuring consistent encryption output for the same inputs.
        """
        if not value:
            return ""
        if self.is_encrypted(value=value):
            return value

        # Derive deterministic salt and rand from key (or password if no key)
        # This ensures the same inputs always produce the same ciphertext
        if not key:
            salt = _randc(1)
            rand = _randc(EXTRA[salt])
        else:
            input_hash = hashlib.sha256(key.encode()).digest()
            salt = NUM_ALPHA[input_hash[0] % len(NUM_ALPHA)]
            rand = "".join(
                NUM_ALPHA[input_hash[1 + i] % len(NUM_ALPHA)]
                for i in range(EXTRA[salt])
            )

        previous = salt
        crypted = MAGIC + salt + rand

        for position, x in enumerate(value):
            encode = ENCODING[position % len(ENCODING)]
            crypted += _gap_encode(x, previous, encode)
            previous = crypted[-1]

        return crypted
