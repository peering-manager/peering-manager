# Jinja2 Filters

Peering Manager exposes functions and filters in additional to existing Jinja2
provided ones. These filters are used to parse, transform, fetch values of
known types. If they are not used as expected, template processing may result
in failure or half rendered texts.

### `safe_string`

Converts a string to another one using only safe characters (retaining only
ASCII characters). This string should be usable in a configuration without
encoding issues.

Example:
```
description "Peering: AS{{ a_s.asn }} {{ a_s.name | safe_string }}"
```

### `tags`

Returns an iterable structure for all tags assigned to an object.

Example:
```
Tags: {{ ixp | tags }}
```

### `ipv4` / `ipv6`

Given an argument, this filter will return a value that can be interpreted as
true or false, for IPv4 or IPv6 respectively. If the value is indeed a valid
IP that matches the filter use, a Python IP address object is returned, thus
allowing getting field values (like version).

Example:
```
{% if session.ip_address | ipv6 %}
```

### `length` / `len` / `count`

Determines the length/count of an object list, dictionary or SQL result.

Example:
```
{% if 10 == internet_exchanges | length %}
```

### `filter`

Allows to pass a Django filter expression to allow filtering on a SQL result.

Example:
```
{% for autonomous_system in autonomous_systems | filter(ipv6_max_prefixes__gt=100) %}
```

### `iterate`

Allows to select and to return the value of a single field for each object in
a list. The field name must be passed as a string.

Example:
```
ASNs: {{ autonomous_systems | iterate('asn') }}
```

### `ixps`

On an autonomous system, it will return all IXPs on which a local (affiliated)
AS is peering with the remote AS. The second `local_as` parameter is mandatory
to use this filter.

Example:
```
{% for ixp in autonomous_system | ixps(local_as) %}
```

### `shared_ixps`

On an autonomous system, it will return all IXPs on which a local (affiliated)
AS could peer with the remote AS. The second `local_as` parameter is mandatory
to use this filter.

This filter is different from `ixps` as it will give back all IXPs the two AS
are peering on in addition to the ones they do not peer on yet.

Example:
```
{% for ixp in autonomous_system | shared_ixps(local_as) %}
```

### `missing_sessions`

On an autonomous system, it will return all sessions that can be configured
between two autonomous systems. You must provide a second AS, providing an IXP
is optional.

Example:
```
{% for missing in autonomous_system | missing_sessions(local_as) %}
IPv4: {{ missing.ipaddr4 }}
IPv6: {{ missing.ipaddr6 }}
{% endfor %}
```

### `prefix_list`

Fetches all the prefixes of an autonomous system and returns them as a JSON
formatted object. Prefixes are fetched using `bgpq3` (or `bgpq4`) but can
come from the local cache if present.

Example:
```
{% set prefixes = autonomous_system | prefix_list %}
```

### `sessions` / `route_server`

When using `sessions` on a BGP group or an IXP, peering sessions setup in the
group or on the IXP will be returned as an iterable object. `route_server`
works similarly but will only give back sessions setup with route servers on
an IXP.

When used on an autonomous system, the `sessions` filter will return all BGP
sessions setup with the AS (direct and IXP sessions).

Examples:
```
{% for session in ixp | sessions %}
{% for session in autonomous_system | sessions %}
{% for session in ixp | route_server(6) %}
```

### `local_ips`

Applied on a session, the filter will fetch the local IP used to establish the
session. If applied on an IXP or a BGP group, it will return IP addresses (v4
and v6) configured for the IXP/BGP group. In any other case, it will give
back a null value.

Examples:
```
Local IPs: {{ session | local_ips }}
Local IPs: {{ ixp | local_ips }}
```

### `direct_sessions` / `ixp_sessions`

When used on an autonomous system, it will return direct peering sessions or
respectively IXP peering sessions setup with the AS. If `4` or `6` is passed
as extra parameter, only the sessions with a IP version matching will be
returned.

Examples:
```
{% for session in autonomous_system | direct_sessions %}
{% for session in autonomous_system | ixp_sessions(6) %}
```

### `ip_version`

For a BGP session, it will return the IP version of the session given the IP
address field.

Example:
```
{% if 6 == session | ip_version %}
```

### `max_prefix`

For a BGP session, it will return the max prefix value corresponding to the
remote AS and the IP address family.

Example:
```
unicast {
    prefix-limit {
        maximum {{ session | max_prefix }};
    }
}
```

### `cisco_password`

From a valid Cisco type 7 password, returns the password stripping the magic
word prefix.

Example:
```
{% if session.encrypted_password %}
password encrypted {{ session.encrypted_password | cisco_password }}
{% elif session.password %}
password clear {{ session.password }}
{% endif %}
```

### `direct_peers` / `ixp_peers`

For a router, fetches all peers connected to it. When using `direct_peers`
only peers with at least one direct peering session will be fetched while
`ixp_peers` will fetch peers with at least on peering session setup on an IXP
connected to the router.

Both filters can optionally take a slug value (as a string) to fetch sessions
from a specific BGP group or IXP.

Example:
```
{% for session in router | ixp_peers %}
...
{% for session in router | direct_peers('transit') %}
```

### `iter_export_policies` / `iter_import_policies`

Fetches routing policies applied on export or on import of an object. Note
that these filters will not traverse relationships, therefore, they will not
fetch AS policies for a session (for instance).

You can use a string as an option to these filters to select only a specific
field of the policies.

Example:
```
export [ {{ session | iter_export_policies('slug') | join(' ') }} ];
import [ {{ session | iter_import_policies('slug') | join(' ') }} ];
```

### `merge_export_policies` / `merge_import_policies`

Merges all import or export routing policies from an object into a single
list. Policies are sorted based on their origin (AS/IXP/Session) and their
weight.

Note that a IXP policy is less preferred than an AS policy. Session policies
are the preferred ones. If a policy is referenced more than one time in the
policy list, only the most preferred occurence will be kept.

The keyword (as a string) `reverse` can be used as option to these two filters
to reverse the order of the list.

Example:
```
export [ {{ session | merge_export_policies | iterate('slug') | join(' ') }} ];
import [ {{ session | merge_import_policies('reverse') | iterate('slug') | join(' ') }} ];
```
