# Optional Configuration Settings

## BASE_PATH

Default: `None`

The base URL path to use when accessing Peering Manager. Do not include the
scheme or domain name. For example, if installed at [http://example.com/peering/],
set:

```no-highlight
BASE_PATH = "peering/"
```

---

## CORS_ORIGIN_ALLOW_ALL

Default: False

If True, cross-origin resource sharing (CORS) requests will be accepted from
all origins. If False, a whitelist will be used (see below).

---

## CORS_ORIGIN_WHITELIST

## CORS_ORIGIN_REGEX_WHITELIST

These settings specify a list of origins that are authorized to make
cross-site API requests. Use `CORS_ORIGIN_WHITELIST` to define a list of exact
hostnames, or `CORS_ORIGIN_REGEX_WHITELIST` to define a set of regular
expressions. (These settings have no effect if `CORS_ORIGIN_ALLOW_ALL` is
True.) For example:

```python
CORS_ORIGIN_WHITELIST = [
    'https://example.com',
]
```

---

## CSRF_COOKIE_NAME

Default: `csrftoken`

The name of the cookie to use for the cross-site request forgery (CSRF)
authentication token. See the
[Django documentation](https://docs.djangoproject.com/en/stable/ref/settings/#csrf-cookie-name)
for more detail.

---

## CSRF_TRUSTED_ORIGINS

Default: `[]`

Defines a list of trusted origins for unsafe (e.g. `POST`) requests. This is a
pass-through to Django's
[`CSRF_TRUSTED_ORIGINS`](https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-CSRF_TRUSTED_ORIGINS)
setting. Note that each host listed must specify a scheme (e.g. `http://` or
`https://).

```python
CSRF_TRUSTED_ORIGINS = (
    'http://peering-manager.local',
    'https://peering-manager.local',
)
```

---

## USE_X_FORWARDED_HOST

Default: `True`

Parse `X-Forwarded-Host` for actual hostname instead of relying on host header.

## SECURE_PROXY_SSL_HEADER

Default: `("HTTP_X_FORWARDED_PROTO", "https")`

Parse defined header to let Django know that HTTPS is being used. This way
e.g. generated API URLs will have the corresponding `https://` prefix.

E.g. `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` to check
for `https` value in `X-Forwarded-Proto` header.

---

## DEBUG

Default: `False`

This setting enables debugging. This should be done only during development or
troubleshooting. Never enable debugging on a production system, as it can
expose sensitive data to users (even unauthenticated).

---

## LOGGING

Default: several files will be used for logging in the `logs` directory.

The Django framework on which Peering Manager runs allows for the customization
of logging, e.g. to write logs to file. Please consult the
[Django logging documentation](https://docs.djangoproject.com/en/3.0/topics/logging/)
for more information on configuring this setting.

---

## RQ_DEFAULT_TIMEOUT

Default: `300`

The maximum execution time of a background task, in seconds.

---

## CACHE_TIMEOUT

Default: `0`

The number of seconds to retain cache entries before automatically invalidating
them. Setting the value to 0 will disable the use of the caching functionality.

---

## CACHE_BGP_DETAIL_TIMEOUT

Default: `900`

The number of seconds to retain cache entries for NAPALM BGP details data
before automatically invalidating them. It improves the speed of operations
such as polling session statuses. Setting the value to 0 will disable the use
of the caching functionality.

---

## CHANGELOG_RETENTION

Default: `90`

The number of days to retain logged changes (object creations, updates, and
deletions). Set this to `0` to retain changes in the database indefinitely.
(Warning: This will greatly increase database size over time having also an
impact on its performances)

---

## JOBRESULT_RETENTION

Default: `90`

The number of days to retain job results. Set this to `0` to retain changes in
the database indefinitely. (Warning: This will greatly increase database size
over time having also an impact on its performances)

---

## LOGIN_REQUIRED

Default: `False`

Setting this to `True` will permit only authenticated users to access Peering
Manager. By default, anonymous users are permitted to access Peering Manager
as read-only.

---

## EMAIL

In order to send email, Peering Manager needs an email server configured. The
following items can be defined within the `EMAIL` setting:

* `SERVER` - Host name or IP address of the email server (use `localhost` if
  running locally)
* `PORT` - TCP port to use for the connection (default: 25)
* `USERNAME` - Username with which to authenticate
* `PASSSWORD` - Password with which to authenticate
* `TIMEOUT` - Time to wait for a connection (in seconds)
* `FROM_ADDRESS` - Sender address for emails sent by Peering Manager
* `SUBJECT_PREFIX` - Prefix of the subject for outgoing emails
* `USE_SSL` - Use implicit TLS connections, usually on port 465
* `USE_TLS` - Use explicit TLS connections, usually on port 587
* `CC_CONTACTS` - Available CC Contacts when sending emails. Formatted like
  `[("email@domain.com", "NOC Contact"), ("other@domain2.com", "NetOps Team")]`

Note that `USE_TLS`/`USE_SSL` are mutually exclusive, so only set one of those
settings to True.

Example:

```no-highlight
EMAIL = {
    'SERVER': 'localhost',
    'FROM_ADDRESS': 'peering-manager@example.net',
    'SUBJECT_PREFIX': '[Peering]'
    'CC_CONTACTS': [
        ('peering@example.net', 'Peering Contact'),
        ('noc@example.net', 'NOC'),
    ]
}
```

---

## HTTP_PROXIES

Default: `None`

A dictionary of HTTP proxies to use for outbound requests originating from
Peering Manager (e.g. requesting PeeringDB synchronisation). Proxies should be
specified by schema (HTTP and HTTPS) as per the Python requests library
documentation. For example:

```no-highlight
HTTP_PROXIES = {
    'http': 'http://10.10.1.10:3128',
    'https': 'http://10.10.1.10:1080',
}
```

---

## JINJA2_TEMPLATE_EXTENSIONS

Default: `[]`

List of Jinja2 extensions to load when rendering templates. Extensions can be
used to add more features to the initial ones. Extensions that are not built
into Jinja2 need to be installed in the Python environment used to run Peering
Manager.

Example:

```no-highlight
JINJA2_TEMPLATE_EXTENSIONS = [
  "jinja2.ext.debug",
  "jinja2.ext.do",
]
```

---

## CONFIG_CONTEXT_RECURSIVE_MERGE / CONFIG_CONTEXT_LIST_MERGE

Default: `True` / `replace`

When merging configuration contexts, Peering Manager needs to know what should
happen to nested dictionaries/hashes and to list. These two options can be
changed to reproduce the wanted behaviour. They are similar to Ansible's
`combine` filter and should produce the same results.

Keep in mind that config contexts are merged in a way that one that has a high
priority will override one with a lower priority.

If `CONFIG_CONTEXT_RECURSIVE_MERGE` is set to `True` (the default value), it
will recursively merge nested hashes.

`CONFIG_CONTEXT_LIST_MERGE` has multiple values possible:
* `replace`: default, arrays in the higher priority config context will
  replace the ones in lower priority config context,
* `keep`: arrays in the lower priority config context will be kept,
* `append`: arrays in the higher priority config context will be appended to
  the ones in the lower priority config context,
* `prepend`: arrays in the higher priority config context will be prepended to
  the ones in the lower priority config context,
* `append_rp`: arrays in the higher priority config context will be appended
  to the ones in the lower priority config context, elements of arrays in that
  are in both config contextes will be removed ("rp" stands for "remove
  present"), duplicate elements that aren’t in both config contexts are kept,
* `prepend_rp`: the behavior is similar to the one for `append_rp`, but
  elements of arrays are prepended.

---

## PEERINGDB_API_KEY

PeeringDB API key used to authenticate against PeeringDB allowing Peering
Manager to synchronise data not accessible without authentication (such as
e-mail contacts).

---

## PEERINGDB_USERNAME / PEERINGDB_PASSWORD

WARNING: DEPRECATED, PLEASE USE `PEERINGDB_API_KEY` INSTEAD.

These settings are being used to authenticate to PeeringDB.

---

## NAPALM_USERNAME / NAPALM_PASSWORD

Peering Manager will use these credentials when authenticating to remote
devices via the [NAPALM library](https://napalm-automation.net/), if installed.
Both parameters are optional but they are required if you want Peering Manager
to push configurations to your devices. They can be overriden on a per-router
basis.

## NAPALM_ARGS

A dictionary of optional arguments to pass to NAPALM when instantiating a
network driver. See the NAPALM documentation for a
[complete list of optional arguments](http://napalm.readthedocs.io/en/latest/support/#optional-arguments).
It can be overriden on a per-router basis.

## NAPALM_TIMEOUT

Default: `30` seconds

The amount of time (in seconds) to wait for NAPALM to connect to a device.
It can be overriden on a per-router basis.

---

## PAGINATE_COUNT

Default: `20`

Determine how many objects to display per page within each list of objects.

---

## TIME_ZONE

Default: `UTC`

The time zone Peering Manager will for date and time operations. Peering Manager will
also attempt to determine this value from `/etc/timezone` before defaulting to UTC.
[List of available time zones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

---

## BGPQ3_PATH

Default: `bgpq3`

The path to the BGPQ3 binary. By default, Peering Manager will look for `bgpq3`
in the system `PATH`. An absolute path to the binary is preferred if you need
to change this setting.

## BGPQ3_HOST

Default: `whois.radb.net`

The host that will be used by BGPQ3 to look for IRR objects.

## BGPQ3_SOURCES

Default: `RIPE,APNIC,AFRINIC,ARIN,NTTCOM,ALTDB,BBOI,BELL,JPIRR,LEVEL3,RADB,RGNET,SAVVIS,TC`

A list of comma separated sources from which we will accept IRR objects.

## BGPQ3_ARGS

Default: `{"ipv6": ["-r", "16", "-R", "48"], "ipv4": ["-r", "8", "-R", "24"]}`

A dictionary with two keys: `ipv6` and `ipv4`. Each value must be a list of
strings to pass to BGPQ3. No spaces are allowed inside strings. If a string has
a space in it, it should be split into two distinct strings.

By default the arguments given will ask BGPQ3 to look for IPv6 prefixes with a
mask length greater than or equal to 16 and less than or equal to 48 and for
IPv4 prefixes with a mask length greater than or equal to 8 and less than or
equal to 24.

---

## NETBOX_API

Default: `None`

The NetBox API URL to which the queries must be sent to.

## NETBOX_API_TOKEN

Default: `None`

The API token registered in the NetBox instance to be used in queries.

## NETBOX_API_THREADING

Default: `False`

Turn on or off threading in some API requests.

## NETBOX_API_VERIFY_SSL

Default: `True`

Turn on or off API SSL certificate verification. Turning it off may be useful
if you use an auto-generated certificate for the NetBox API.

## NETBOX_DEVICE_ROLES

Default: `["router", "firewall"]`

The roles that devices must have in the NetBox instance that will be queried.
Incoming webhooks to process will also check if the device role matches one of
the list. An empty list will match all devices in the NetBox instance.

## NETBOX_TAGS

Default: `[]` (empty list)

The tags that devices must have in the NetBox instance from which incoming
webhooks will be processed. As soon as one tag matches, the webhook will be
accepted.

---

## RELEASE_CHECK_URL

Default: `https://api.github.com/repos/peering-manager/peering-manager/releases`

The URL to detect new releases, which are shown on the home page of the web
interface. You can change this to your own fork, or set it to None to disable
it. The URL provided must be compatible with the GitHub API.

---

## REQUESTS_USER_AGENT

Default: "PeeringManager/x.y"

User agent that Peering Manager will user when making requests to external
HTTP resources. It should probably not be changed unless you have issues with
specific HTTP endpoints.
