from ..enums import PasswordAlgorithm
from .cisco import decrypt as cisco_type7_decrypt
from .cisco import encrypt as cisco_type7_encrypt
from .juniper import decrypt as juniper_type9_decrypt
from .juniper import encrypt as juniper_type9_encrypt
from .nokia import decrypt as nokia_bcrypt_decrypt
from .nokia import encrypt as nokia_bcrypt_encrypt

ENCRYPTERS = {
    PasswordAlgorithm.CISCO_TYPE7: cisco_type7_encrypt,
    PasswordAlgorithm.JUNIPER_TYPE9: juniper_type9_encrypt,
    PasswordAlgorithm.NOKIA_BCRYPT: nokia_bcrypt_encrypt,
}
DECRYPTERS = {
    PasswordAlgorithm.CISCO_TYPE7: cisco_type7_decrypt,
    PasswordAlgorithm.JUNIPER_TYPE9: juniper_type9_decrypt,
    PasswordAlgorithm.NOKIA_BCRYPT: nokia_bcrypt_decrypt,
}

__all__ = ("ENCRYPTERS", "DECRYPTERS")
