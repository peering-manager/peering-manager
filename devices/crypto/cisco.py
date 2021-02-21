import random
import re

# Let's bring some fun, this code is based on the following readings
#
# https://pen-testing.sans.org/resources/papers/gcih/cisco-ios-type-7-password-vulnerability-100566
# http://wiki.nil.com/Deobfuscating_Cisco_IOS_Passwords


MAGIC = "7 "
XLAT = [
    0x64,
    0x73,
    0x66,
    0x64,
    0x3B,
    0x6B,
    0x66,
    0x6F,
    0x41,
    0x2C,
    0x2E,
    0x69,
    0x79,
    0x65,
    0x77,
    0x72,
    0x6B,
    0x6C,
    0x64,
    0x4A,
    0x4B,
    0x44,
    0x48,
    0x53,
    0x55,
    0x42,
    0x73,
    0x67,
    0x76,
    0x63,
    0x61,
    0x36,
    0x39,
    0x38,
    0x33,
    0x34,
    0x6E,
    0x63,
    0x78,
    0x76,
    0x39,
    0x38,
    0x37,
    0x33,
    0x32,
    0x35,
    0x34,
    0x6B,
    0x3B,
    0x66,
    0x67,
    0x38,
    0x37,
]


def is_encrypted(value):
    return value.startswith(MAGIC)


def decrypt(value):
    if not value:
        return ""

    if not is_encrypted(value):
        return value

    value = value.replace(MAGIC, "")

    decrypted = ""

    regex = re.compile("(^[0-9A-Fa-f]{2})([0-9A-Fa-f]+)")
    result = regex.search(value)

    s, e = int(result.group(1), 16), result.group(2)
    for position in range(0, len(e), 2):
        magic = int(e[position] + e[position + 1], 16)
        if s <= 50:
            new_character = format((magic ^ XLAT[s]), "c")
            s += 1
        if s == 51:
            s = 0
        decrypted += new_character

    return decrypted


def encrypt(value):
    if not value:
        return ""

    if is_encrypted(value):
        return value

    salt = random.randrange(0, 15)
    encrypted = format(salt, "02x")

    for i in range(len(value)):
        encrypted += format((ord(value[i]) ^ XLAT[salt]), "02x")
        salt += 1
        if salt == 51:
            salt = 0

    return f"{MAGIC}{encrypted.upper()}"
