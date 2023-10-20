# Required Configuration Settings

## ALLOWED_HOSTS

This is a list of valid fully-qualified domain names (FQDNs) and/or IP
addresses that can be used to reach the Peering Manager service. It can be
different from the name of the server used as URL (e.g. when using a reverse
proxy serving the website under a different FQDN than the hostname of the
Peering Manager server).

Example:

```no-highlight
ALLOWED_HOSTS = ['peering.example.com', '192.0.2.42']
```

---

## DATABASE

Peering Manager requires access to a PostgreSQL database service to store data.
This service can run locally or on a remote system. The following parameters
must be defined within the `DATABASE` dictionary:

* `NAME` - Database name
* `USER` - PostgreSQL username
* `PASSWORD` - PostgreSQL password
* `HOST` - Name or IP address of the database server (use `localhost` if
  running locally)
* `PORT` - TCP port of the PostgreSQL service; leave blank for default port
  (TCP/5432)
* `CONN_MAX_AGE` - Lifetime of a
  [persistent database connection](https://docs.djangoproject.com/en/stable/ref/databases/#persistent-connections), in seconds (300 is the default)

Example:

```no-highlight
DATABASE = {
    'NAME': 'peering-manager',        # Database name
    'USER': 'peering-manager',        # PostgreSQL username
    'PASSWORD': 'v3rys3cur3passw0rd', # PostgreSQL password
    'HOST': 'localhost',              # Database server
    'PORT': '',                       # Database port (leave blank for default)
}
```

!!! note
    Peering Manager supports all PostgreSQL database options supported by the
    underlying Django framework. For a complete list of available parameters,
    please see [the Django documentation](https://docs.djangoproject.com/en/stable/ref/settings/#databases).

---

## REDIS

[Redis](https://redis.io/) is an in-memory data store similar to memcached. It
is required to support task scheduling and caching features.

Redis is configured using a configuration setting similar to `DATABASE` except
you need to have two different instances, one for tasks and one for caching.

* `HOST` - Name or IP address of the Redis server (use localhost if running
  locally)
* `PORT` - TCP port of the Redis service; leave blank for default port (6379)
* `USERNAME` - Redis username (if set)
* `PASSWORD` - Redis password (if set)
* `DATABASE` - Numeric database ID
* `SSL` - Use SSL connection to Redis
* `INSECURE_SKIP_TLS_VERIFY` - Set to True to disable TLS certificate
  verification (not recommended)

An example configuration is provided below:

```no-highlight
REDIS = {
    'tasks': {
        'HOST': 'redis.example.com',
        'PORT': 1234,
        'USERNAME': 'peeringmanager'
        'PASSWORD': 'securepassword',
        'DATABASE': 0,
        'SSL': False,
    },
    'caching': {
        'HOST': 'localhost',
        'PORT': 6379,
        'USERNAME': ''
        'PASSWORD': '',
        'DATABASE': 1,
        'SSL': False,
    }
}
```

!!! warning
    It is highly recommended to keep the task and cache databases separate.
    Using the same database number on the same Redis instance for both may
    result in unexpected side-effects such as data loss.

If you are using [Redis Sentinel](https://redis.io/topics/sentinel) for
high-availability purposes, there is minimal configuration necessary to
convert for Peering Manager to recognize it. It requires the removal of the
`HOST` and `PORT` keys from above and the addition of three new keys.

* `SENTINELS`: List of tuples or tuple of tuples with each inner tuple
  containing the name or IP address of the Redis server and port for each
  sentinel instance to connect to
* `SENTINEL_SERVICE`: Name of the master / service to connect to
* `SENTINEL_TIMEOUT`: Connection timeout, in seconds

Example:

```no-highlight
REDIS = {
    'tasks': {
        'SENTINELS': [('mysentinel.redis.example.com', 6379)],
        'SENTINEL_SERVICE': 'peeringmanager',
        'SENTINEL_TIMEOUT': 10,
        'PASSWORD': '',
        'DATABASE': 0,
        'SSL': False,
    },
    'caching': {
        'SENTINELS': [
            ('mysentinel.redis.example.com', 6379),
            ('othersentinel.redis.example.com', 6379)
        ],
        'SENTINEL_SERVICE': 'peeringmanager',
        'PASSWORD': '',
        'DATABASE': 1,
        'SSL': False,
    }
}
```

!!! note
    It is possible to use Sentinel for only one database and not the other.

---

## SECRET_KEY

This is a secret cryptographic key is used to improve the security of cookies
and password resets. The key defined here should not be shared outside of the
configuration file. `SECRET_KEY` can be changed at any time, however be aware
that doing so will invalidate all existing sessions.

Please note that this key is **not** used for hashing user passwords.

`SECRET_KEY` should be at least 50 characters in length and contain a random
mix of letters, digits, and symbols.
