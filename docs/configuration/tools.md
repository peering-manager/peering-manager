# Optional Configuration Settings


## CACHE_BGP_DETAIL_TIMEOUT

Default: `900`

The number of seconds to retain cache entries for NAPALM BGP details data
before automatically invalidating them. It improves the speed of operations
such as polling session statuses. Setting the value to 0 will disable the use
of the caching functionality.

---

## PEERINGDB_API_KEY

PeeringDB API key used to authenticate against PeeringDB allowing Peering
Manager to synchronise data not accessible without authentication (such as
e-mail contacts).

---

## PEERINGDB_USERNAME / PEERINGDB_PASSWORD

!!! warn
    These settings are deprecated, use `PEERINGDB_API_KEY` instead.

Username and password used for PeeringDB API authentication.

---

## NAPALM_USERNAME / NAPALM_PASSWORD

Peering Manager will use these credentials when authenticating to remote
devices via the [NAPALM library](https://napalm-automation.net/), if installed.
Both parameters are optional but they are required if you want Peering Manager
to push configurations to your devices. They can be overriden on a per-router
basis.

---

## NAPALM_ARGS

A dictionary of optional arguments to pass to NAPALM when instantiating a
network driver. See the NAPALM documentation for a
[complete list of optional arguments](http://napalm.readthedocs.io/en/latest/support/#optional-arguments).
It can be overriden on a per-router basis.

---

## NAPALM_TIMEOUT

Default: `30` seconds

The amount of time (in seconds) to wait for NAPALM to connect to a device.
It can be overriden on a per-router basis.

---

## BGPQ3_PATH

Default: `bgpq3`

The path to the bgpq3 or bgpq4 binary. By default, Peering Manager will look
for `bgpq3` in the system `PATH`. An absolute path to the binary is preferred
if you need to change this setting.

---

## BGPQ3_HOST

Default: `rr.ntt.net`

The host that will be used by BGPQ3 to look for IRR objects.

---

## BGPQ3_SOURCES

Default: `RPKI,RIPE,ARIN,APNIC,AFRINIC,LACNIC`

A list of comma separated sources from which we will accept IRR objects.

---

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

---

## NETBOX_API_TOKEN

Default: `None`

The API token registered in the NetBox instance to be used in queries.

---

## NETBOX_API_THREADING

Default: `False`

Turn on or off threading in some API requests.

---

## NETBOX_API_VERIFY_SSL

Default: `True`

Turn on or off API SSL certificate verification. Turning it off may be useful
if you use an auto-generated certificate for the NetBox API.

---

## NETBOX_DEVICE_ROLES

Default: `["router", "firewall"]`

The roles that devices must have in the NetBox instance that will be queried.
Incoming webhooks to process will also check if the device role matches one of
the list. An empty list will match all devices in the NetBox instance.

---

## NETBOX_TAGS

Default: `[]` (empty list)

The tags that devices must have in the NetBox instance from which incoming
webhooks will be processed. As soon as one tag matches, the webhook will be
accepted.
