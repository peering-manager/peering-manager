# Required Configuration Settings

## ALLOWED_HOSTS

This is a list of valid fully-qualified domain names (FQDNs) and/or IP
addresses that is used to reach the Peering Manager service. It can be
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

  * NAME - Database name
  * USER - PostgreSQL username
  * PASSWORD - PostgreSQL password
  * HOST - Name or IP address of the database server (use `localhost` if
    running locally)
  * PORT - TCP port of the PostgreSQL service; leave blank for default port
    (5432)

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

---

## REDIS

[Redis](https://redis.io/) is an in-memory data store similar to memcached. It
is required to support task scheduling and caching features.

Redis is configured using a configuration setting similar to `DATABASE` except
you need to have two different instances, one for tasks and one for caching.

For each instance the following settings must be defined:

* `HOST` - Name or IP address of the Redis server (use `localhost` if running locally)
* `PORT` - TCP port of the Redis service; leave blank for default port (6379)
* `PASSWORD` - Redis password (if set)
* `CACHE_DATABASE` - Numeric database ID for caching
* `DEFAULT_TIMEOUT` - Connection timeout in seconds
* `SSL` - Use SSL connection to Redis

Example:

```
REDIS = {
    'tasks': {
        'HOST': 'localhost',
        'PORT': 6379,
        'PASSWORD': '',
        'CACHE_DATABASE': 0,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    },
    'caching': {
        'HOST': 'localhost',
        'PORT': 6379,
        'PASSWORD': '',
        'CACHE_DATABASE': 1,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    }
}
```

It is highly recommended to keep the task and cache databases separate. Using
the same database number on the same Redis instance for both may result in
unexpected side-effects such as data loss.

---

## SECRET_KEY

This is a secret cryptographic key is used to improve the security of cookies
and password resets. The key defined here should not be shared outside of the
configuration file. `SECRET_KEY` can be changed at any time, however be aware
that doing so will invalidate all existing sessions.

Please note that this key is **not** used for hashing user passwords.

`SECRET_KEY` should be at least 50 characters in length and contain a random
mix of letters, digits, and symbols.
