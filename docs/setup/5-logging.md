Peering Manager provides some loggers to make sure logs can be processed by any
means a user may want to use. By default no logging is configured, a working
example is provided below.

# Available Loggers

Loggers are points where logs are sent for processing. The following
loggers are provided:

* `peering.manager.devices`: logging internal models and views
* `peering.manager.extras`: logging webhooks and other
* `peering.manager.napalm`: logging actions done by NAPALM
* `peering.manager.net`: logging internal models and views
* `peering.manager.netbox`: logging actions related to NetBox
* `peering.manager.peering`: logging internal models and views
* `peering.manager.peeringdb`: logging actions related to PeeringDB
* `peering.manager.releases`: logging new release monitoring

To adjust the logging configuration to your needs, you probably want to read
[Django's documentation](https://docs.djangoproject.com/en/stable/topics/logging/)
about it. Have a look at
[Python logging dictionary schema](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema)
as well. Apply any required `LOGGING` modifications to
`peering_manager/configuration.py`.

# Example

This example will format logs using the `simple` formatter defined below and
will separate logs in files depending of the loggers. Each file will contain a
day of logs, 5 days will be kept.

With this configuration, logs about releases will be displayed in the console
while logs about PeeringDB will be stored in the
`/opt/peering-manager/logs/peeringdb.log` file.

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
        "peeringdb_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "/opt/peering-manager/logs/peeringdb.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "formatter": "simple",
        },
    },
    "loggers": {
        "peering.manager.peeringdb": {"handlers": ["peeringdb_file"], "level": "DEBUG"},
        "peering.manager.releases": {"handlers": ["console"], "level": "DEBUG"},
    },
}
```
