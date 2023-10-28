import bcrypt
#
# Implements a custom AES256 based password encryption scheme
#
# Note: router must be configured accordingly:
# /admin system security hash-control custom-hash algorithm aes256 key "09123456789012345678901234567890"
#
# Considered generating a unique random key for each router, but it would still have to 
# be embedded in the same config file -> offers little additional security, just more 
# complexity
#

# KEY = hashlib.sha256(passphrase).digest()# returns 256 bit key
KEY = "09123456789012345678901234567890".encode('ascii') # 32-character magic key, must match router

#
# Hashing algorithm only used for encryption, decrypt is no-op
#
def decrypt(value):
  return value

def encrypt(value, salt=None):
  if not value:
    return ""

  if not salt:
    salt = bcrypt.gensalt(rounds=10)

  return bcrypt.hashpw(value.encode('utf-8'), salt).decode('utf-8')
