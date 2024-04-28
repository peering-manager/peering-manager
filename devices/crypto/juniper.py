import random

# This code is the result of the attempt at converting a Perl module, the expected
# result might not actually be what we really want it to be ¯\_(ツ)_/¯
#
# https://metacpan.org/pod/Crypt::Juniper

__all__ = ("is_encrypted", "decrypt", "encrypt")

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


def __nibble(cref, length):
    nib = cref[0:length]
    rest = cref[length:]

    if len(nib) != length:
        raise Exception(f"Ran out of characters: hit '{nib}', expecting {length} chars")

    return nib, rest


def __gap(c1, c2):
    return (ALPHA_NUM[str(c2)] - ALPHA_NUM[str(c1)]) % (len(NUM_ALPHA)) - 1


def __gap_decode(gaps, dec):
    num = 0

    if len(gaps) != len(dec):
        raise Exception("Nibble and decode size not the same.")

    for x in range(len(gaps)):
        num += gaps[x] * dec[x]

    return chr(num % 256)


def __reverse(current):
    reversed = list(current)
    reversed.reverse()
    return reversed


def __gap_encode(pc, prev, encode):
    __ord = ord(pc)

    crypt = ""
    gaps = []
    for mod in __reverse(encode):
        gaps.insert(0, int(__ord / mod))
        __ord %= mod

    for gap in gaps:
        gap += ALPHA_NUM[prev] + 1
        prev = NUM_ALPHA[gap % len(NUM_ALPHA)]
        crypt += prev

    return crypt


def __randc(counter=0):
    return_value = ""
    for _ in range(counter):
        return_value += NUM_ALPHA[random.randrange(len(NUM_ALPHA))]
    return return_value


def is_encrypted(value):
    return value.startswith(MAGIC)


def decrypt(value):
    if not value:
        return ""

    if not is_encrypted(value):
        return value

    chars = value.split("$9$", 1)[1]
    first, chars = __nibble(chars, 1)
    toss, chars = __nibble(chars, EXTRA[first])
    previous = first
    decrypted = ""

    while chars:
        decode = ENCODING[len(decrypted) % len(ENCODING)]
        nibble, chars = __nibble(chars, len(decode))
        gaps = []
        for i in nibble:
            g = __gap(previous, i)
            previous = i
            gaps += [g]
        decrypted += __gap_decode(gaps, decode)

    return decrypted


def encrypt(value, salt=None):
    if not value:
        return ""

    if is_encrypted(value):
        return value

    if not salt:
        salt = __randc(1)
    rand = __randc(EXTRA[salt])

    position = 0
    previous = salt
    crypted = MAGIC + salt + rand

    for x in value:
        encode = ENCODING[position % len(ENCODING)]
        crypted += __gap_encode(x, previous, encode)
        previous = crypted[-1]
        position += 1

    return crypted
