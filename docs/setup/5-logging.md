Peering Manager provides some loggers to make sure logs can be processed by any
means a user may want to use. By default no logging is configured, a working
example is provided below.

# Available Loggers

Loggers are points where logs are send to for latter processing. The following
loggers are provided:

  * `peering.manager.peering`: used to log Peering Manager actions
  * `peering.manager.peeringdb`: used to log actions related to PeeringDB
  * `peering.manager.napalm`: used to log actions done by NAPALM
  * `peering.manager.netbox`: used to log actions related to NetBox

To adjust the logging configuration to your needs, you probably want to read
[Django's documentation](https://docs.djangoproject.com/en/2.1/topics/logging/)
about it. Apply any required `LOGGING` modifications to
`peering_manager/configuration.py`.

# Example

This example will format logs using the `simple` formatter defined below and
will separate logs in files depending of the loggers. Each file will contain a
day of logs, 5 days will be kept.

```no-highlight
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
```
