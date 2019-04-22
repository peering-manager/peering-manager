# This is a list of valid fully-qualified domain names (FQDNs) for this server.
# The server will not permit write access to the server via any other
# hostnames. The first FQDN in the list will be treated as the preferred name.
#
# Example: ALLOWED_HOSTS = ['peering.example.com', 'peering.internal.local']
import os
ALLOWED_HOSTS = ["*"]

# Must be unique to each setup (CHANGE IT!).
SECRET_KEY = "ef7npku*djrj_r4jt4cojo8^j@2($$@05e(eq_mn!ywx*jg0vy"

VERSION = "v0.99-dev ($Id$)"

BASE_PATH = ""

TIME_ZONE = os.environ['TIME_ZONE']
MY_ASN = os.environ['MY_ASN']
DATABASE = {
  'NAME': os.environ['DATABASE_NAME'],
  'USER': os.environ['DATABASE_USER'],
  'PASSWORD': os.environ['DATABASE_PASSWORD'],
  'HOST': 'db',
}
