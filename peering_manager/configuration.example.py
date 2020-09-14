# This is a list of valid fully-qualified domain names (FQDNs) for this server.
# The server will not permit write access to the server via any other
# hostnames. The first FQDN in the list will be treated as the preferred name.
#
# Example: ALLOWED_HOSTS = ['peering.example.com', 'peering.internal.local']
ALLOWED_HOSTS = ["*"]

# Must be unique to each setup (CHANGE IT!).
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
        "CACHE_DATABASE": 0,
        "DEFAULT_TIMEOUT": 300,
        "SSL": False,
    },
    "caching": {
        "HOST": "localhost",
        "PORT": 6379,
        "PASSWORD": "",
        "CACHE_DATABASE": 1,
        "DEFAULT_TIMEOUT": 300,
        "SSL": False,
    },
}
# Cache timeout in seconds. Set to 0 to disable caching.
CACHE_TIMEOUT = 900

LOGIN_REQUIRED = True
