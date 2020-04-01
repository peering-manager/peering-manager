# This is a list of valid fully-qualified domain names (FQDNs) for this server.
# The server will not permit write access to the server via any other
# hostnames. The first FQDN in the list will be treated as the preferred name.
#
# Example: ALLOWED_HOSTS = ['peering.example.com', 'peering.internal.local']
import os
ALLOWED_HOSTS = ["*"]

# Must be unique to each setup (CHANGE IT!).
SECRET_KEY = os.environ['SECRET_KEY']

BASE_PATH = ""

TIME_ZONE = os.environ['TZ']
MY_ASN = os.environ['MY_ASN']

DATABASE = {
  'NAME': os.environ['POSTGRES_DB'],
  'USER': os.environ['POSTGRES_USER'],
  'PASSWORD': os.environ['POSTGRES_PASSWORD'],
  'HOST': os.environ['DATABASE_HOST'],
}

PEERINGDB_USERNAME = os.environ['PEERINGDB_USERNAME']
PEERINGDB_PASSWORD = os.environ['PEERINGDB_PASSWORD']

NAPALM_USERNAME = os.environ['NAPALM_USERNAME']
NAPALM_PASSWORD = os.environ['NAPALM_PASSWORD']

LOGGING = {
    "version": 1,
    "formatters": {
        "simple": {
            "format": "%(asctime)s | %(levelname)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/peering-manager.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "formatter": "simple",
        },
        "peeringdb_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/peeringdb.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "formatter": "simple",
        },
        "napalm_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/napalm.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "formatter": "simple",
        },
        "netbox_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/netbox.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "formatter": "simple",
        },
    },
    "loggers": {
        "peering.manager.peering": {"handlers": ["file"], "level": "DEBUG"},
        "peering.manager.peeringdb": {"handlers": ["peeringdb_file"], "level": "DEBUG"},
        "peering.manager.napalm": {"handlers": ["napalm_file"], "level": "DEBUG"},
        "peering.manager.netbox": {"handlers": ["netbox_file"], "level": "DEBUG"},
    },
}