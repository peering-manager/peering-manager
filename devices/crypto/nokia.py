import bcrypt

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
