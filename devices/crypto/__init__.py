from devices.enums import PasswordAlgorithm

from .cisco import decrypt as cisco_type7_decrypt
from .cisco import encrypt as cisco_type7_encrypt
from .juniper import decrypt as juniper_type9_decrypt
from .juniper import encrypt as juniper_type9_encrypt

ENCRYPTERS = {
    PasswordAlgorithm.CISCO_TYPE7: cisco_type7_encrypt,
    PasswordAlgorithm.JUNIPER_TYPE9: juniper_type9_encrypt,
}
DECRYPTERS = {
    PasswordAlgorithm.CISCO_TYPE7: cisco_type7_decrypt,
    PasswordAlgorithm.JUNIPER_TYPE9: juniper_type9_decrypt,
}

__all__ = ("ENCRYPTERS", "DECRYPTERS")
