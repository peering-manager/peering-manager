# Optional Configuration Settings

## BASE_PATH

Default: None

The base URL path to use when accessing Peering Manager. Do not include the
theme or domain name. For example, if installed at [http://example.com/peering/],
set:

```no-highlight
BASE_PATH = "peering/"
```

---

## DEBUG

Default: `False`

This setting enables debugging. This should be done only during development or
troubleshooting. Never enable debugging on a production system, as it can
expose sensitive data to users (even unauthenticated). Note that if you enable
debugging you **must** install requirements found in `requirements_dev.txt`.

---

## LOGGING

Default: several files will be used for logging in the `logs` directory.

The Django framework on which Peering Manager runs allows for the customization
of logging, e.g. to write logs to file. Please consult the
[Django logging documentation](https://docs.djangoproject.com/en/3.0/topics/logging/)
for more information on configuring this setting.

---

## CACHE_TIMEOUT

Default: 0

The number of seconds to retain cache entries before automatically invalidating
them. Setting the value to 0 will disable the use of the caching functionality.

---

## CHANGELOG_RETENTION

Default: `90`

The number of days to retain logged changes (object creations, updates, and
deletions). Set this to `0` to retain changes in the database indefinitely.
(Warning: This will greatly increase database size over time having also an
impact on its performances)

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

---

## PEERINGDB_API_KEY

PeeringDB API key used to authenticate against PeeringDB allowing Peering
Manager to synchronize data not accessible without authentication (such as
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

### BGPQ3_ARGS

Default: `{"ipv6": ["-r", "16", "-R", "48"], "ipv4": ["-r", "8", "-R", "24"]}`

A dictionary with two keys: `ipv6` and `ipv4`. Each value must be a list of
strings to pass to BGPQ3. No spaces are allowed inside strings. If a string has
a space in it, it should be split into two distinct strings.

By default the arguments given will ask BGPQ3 to look for IPv6 prefixes with a
mask length greater than or equal to 16 and less than or equal to 48 and for
IPv4 prefixes with a mask length greater than or equal to 8 and less than or
equal to 24.

---

### NETBOX_API

Default: `None`

The NetBox API URL to which the queries must be sent to.

### NETBOX_API_TOKEN

Default: `None`

The API token registered in the NetBox instance to be used in queries.

### NETBOX_API_THREADING

Default: `False`

Turn on or off threading in some API requests.

### NETBOX_API_VERIFY_SSL

Default: `True`

Turn on or off API SSL certificate verification. Turning it off may be useful
if you use an auto-generated certificate for the NetBox API.

### NETBOX_DEVICE_ROLES

Default: `["router", "firewall", "switch"]`

The roles that devices must have in the NetBox instance that will be queried.

---

### RELEASE_CHECK_URL

Default: "https://api.github.com/repos/peering-manager/peering-manager/releases"

The URL to detect new releases, which are shown on the home page of the web
interface. You can change this to your own fork, or set it to None to disable
it. The URL provided must be compatible with the GitHub API.

### RELEASE_CHECK_TIMEOUT

Default: 86400 (24 hours)

The number of seconds to retain the latest version that is fetched from the
GitHub API before fetching it from the API again. This value cannot be set to
less than 3600 seconds (1 hour).
