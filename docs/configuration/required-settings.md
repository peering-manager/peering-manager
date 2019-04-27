# Required Configuration Settings

## MY_ASN

---

## ALLOWED_HOSTS

This is a list of valid fully-qualified domain names (FQDNs) and/or IP
addresses that is used to reach the Peering Manager service. It can be
different from the name of the server used as URL (e.g. when using a reverse
proxy serving the website under a different FQDN than the hostname of the
Peering Manager server).

Example:

```no-highlight
ALLOWED_HOSTS = ['peering.example.com', '192.168.42.42']
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

## SECRET_KEY

This is a secret cryptographic key is used to improve the security of cookies
and password resets. The key defined here should not be shared outside of the
configuration file. `SECRET_KEY` can be changed at any time, however be aware
that doing so will invalidate all existing sessions.

Please note that this key is **not** used for hashing user passwords.

`SECRET_KEY` should be at least 50 characters in length and contain a random
mix of letters, digits, and symbols.
