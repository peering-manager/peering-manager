# This is a list of valid fully-qualified domain names (FQDNs) for this server.
# The server will not permit write access to the server via any other
# hostnames. The first FQDN in the list will be treated as the preferred name.
#
# Example: ALLOWED_HOSTS = ['peering.example.com', 'peering.internal.local']
ALLOWED_HOSTS = ["*"]

# Must be unique to each setup (CHANGE IT!).
# A random one can be generated with Python in the Peering Manager venv with
# from django.core.management.utils import get_random_secret_key
# get_random_secret_key()
SECRET_KEY = "ef7npku*djrj_r4jt4cojo8^j@2($$@05e(eq_mn!ywx*jg0vy"

# Base URL path if accessing Peering Manager within a directory.
BASE_PATH = ""

# Time zone to use for date.
TIME_ZONE = "Europe/Paris"

# PostgreSQL database configuration
DATABASE = {
    "NAME": "peering_manager",  # Database name
    "USER": "devbox",  # PostgreSQL username
    "PASSWORD": "devbox",  # PostgreSQL password
    "HOST": "localhost",  # Database server
    "PORT": "",  # Database port (leave blank for default)
}

# Redis configuration
REDIS = {
    "tasks": {
        "HOST": "localhost",
        "PORT": 6379,
        "PASSWORD": "",
        "DATABASE": 0,
        "SSL": False,
    },
    "caching": {
        "HOST": "localhost",
        "PORT": 6379,
        "PASSWORD": "",
        "DATABASE": 1,
        "SSL": False,
    },
}
# Maximum execution time for background tasks, in seconds.
RQ_DEFAULT_TIMEOUT = 3600

LOGIN_REQUIRED = True

# Token Object Permissions - Default behavior when no explicit permission exists
# Set to "allow" (default) for permissive mode - tokens can do everything unless restricted
# Set to "deny" for restrictive mode - tokens can do nothing unless explicitly allowed
# TOKEN_PERMISSIONS_DEFAULT_MODE = "allow"
