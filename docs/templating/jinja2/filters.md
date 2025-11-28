# Jinja2 Filters

Peering Manager exposes functions and filters in addition to existing Jinja2
provided ones. These filters are used to parse, to transform or to fetch
values. If they are not used as expected, template processing may result in
failure or half rendered texts.

## `include_configuration` / `include_email` / `include_exporttemplate`

Includes the configuration template or the e-mail body defined in another
object. It is useful to divide a big template into smaller ones for ease of
management. The context and extensions are passed to the included templates
except for the export template include statement.

In the case of export template, the one that is imported is evaluated before
its actual import which means that it is rendered independently before being
printed into the main template.

`include_*` functions take a template name or a template ID as a parameter.

Examples:

```no-highlight
{% include_configuration "BGP Groups" %}
{% include_configuration "BGP Sessions" %}
{% include_configuration "BGP Policies" %}
{% include_exporttemplate "IXPs" %}
```

```no-highlight
{% include_email 1 %} {# ID of the e-mail object #}
```

## `safe_string`

Converts a string to another one using only safe characters (retaining only
ASCII characters). This string should be usable in a configuration without
encoding issues.

Example:

```no-highlight
description "Peering: AS{{ a_s.asn }} {{ a_s.name | safe_string }}"
```

## `quote`

Quote a value before displaying it as a string. The character/string used for
quotation can be changed by using a second parameter to the filter. Default
quotation character is `"`.

Examples:

```no-highlight
community {{ community.slug }} members {{ community.value | quote }}
description {{ autonomous_system | quote('--') }}
```

## `tags`

Returns an iterable structure for all tags assigned to an object.

Example:

```no-highlight
Tags: {{ ixp | tags }}
```

## `has_tag` / `has_not_tag`

Returns a boolean telling if a tag is or is not applied to an object.

Example:

```no-highlight
{% if ixp | has_tag('remote-peering') %}
{% if ixp | has_not_tag('remote-peering') %}
```

## `ipv4` / `ipv6`

Given an argument, this filter will return a value that can be interpreted as
true or false, for IPv4 or IPv6 respectively. If the value is indeed a valid
IP that matches the filter use, a Python IP address object is returned, thus
allowing getting field values (like version).

Example:

```no-highlight
{% if session.ip_address | ipv6 %}
```

## `ip`

Returns the IP address without the prefix length for a BGP session or IP
address fields. The returned value is a string. If a list is given, each item
of the list will be processed and returned as a list as well.

Examples:

```no-highlight
{% for session in ixp | sessions %}
Remote: {{ session | ip }}
{% if session.local_ip_address %}
Local: {{ session.local_ip_address | ip }}
{% endif %}
{% endfor %}
```

## `mac`

Returns the MAC address as a lowercased string given a format.

Accepted formats are:

* `cisco`: `001b.7749.54fd`
* `bare`: `001b774954fd`

If no format is given, it'll default to the UNIX one: `00:1b:77:49:54:fd`.

Examples:

```no-highlight
MAC address: {{ connection | mac }}
MAC address: {{ connection.mac_address | mac('cisco') }}
```

## `inherited_status`

Returns the status of an object if it has any.

If the status of the object is equivalent to a disabled one, the status of the
parent will not be resolved as this kind of status is considered more
specific.

In case of connections, both IXP's and router's statuses will be checked
(IXP's first).

In case of direct peering sessions, both group's and router's statuses will be
checked (group's first).

In case of IXP peering sessions, connection's status will be checked but that
will trigger a recursive check for it which means it'll take into account the
IXP or router status.

Example:

```no-highlight
{% for session in ixp | sessions %}
{% if session | inherited_status != "enabled" %}
{{ session | ip }} is not enabled
{% endif %}
{% endfor %}
```

## `length` / `len` / `count`

Determines the length/count of an object list, dictionary or SQL result.

Example:

```no-highlight
{% if 10 == internet_exchanges | length %}
```

## `filter`

Allows to pass a Django filter expression to allow filtering on a SQL result.
It can also filter a list of items given attributes and their values.

Examples:

```no-highlight
{% for autonomous_system in autonomous_systems | filter(ipv6_max_prefixes__gt=100) %}
{% for session in bgpgroup | session | filter(router=router) %}
{% for community in session | merge_communities | filter(type='ingress') %}
```

## `get`

Allows to pass a Django filter expression to allow filtering on a SQL result
and return a single object. If more than one object match the filter, this
filter will behave in the exact same way as `filter`.

Example:

```no-highlight
My AS is {{ affiliated_autonomous_systems | get(asn=64500) }}
```

## `unique_items`

Keeps only unique items given a field in a list. Uniqueness is based on the
field value.

Example:

```no-highlight
{% for session in dataset | unique_items("autonomous_system") %}
...
{% endfor %}
```

## `iterate`

Allows to select and to return the value of a single field for each object in
a list. The field name must be passed as a string.

Example:

```no-highlight
ASNs: {{ autonomous_systems | iterate('asn') }}
```

## `ixps`

On an autonomous system, it will return all IXPs on which a local (affiliated)
AS is peering with the remote AS. The second `local_as` parameter is mandatory
to use this filter.

Example:

```no-highlight
{% for ixp in autonomous_system | ixps(local_as) %}
```

## `shared_ixps`

On an autonomous system, it will return all IXPs on which a local (affiliated)
AS could peer with the remote AS. The second `local_as` parameter is mandatory
to use this filter.

This filter is different from `ixps` as it will give back all IXPs the two AS
are peering on in addition to the ones they do not peer on yet.

Example:

```no-highlight
{% for ixp in autonomous_system | shared_ixps(local_as) %}
```

## `shared_facilities`

On an autonomous system, it will return all facilities in which both the AS
and another local (affiliated) AS are according to their respective PeeringDB
records. If one of the autonomous systems has not PeeringDB record or if no
PeeringDB local cache is present, this filter will return an empty iterable.

Example:

```no-highlight
{% for facility in autonomous_system | shared_facilities(local_as) %}
- {{ facility }}
{% endfor %}
```

## `missing_sessions`

On an autonomous system, it will return all sessions that can be configured
between two autonomous systems. You must provide a second AS, providing an IXP
is optional.

When one of the parameters is a PeeringDB network object, e.g. when used to
send an e-mail to an AS unknown to Peering Manager, all possible sessions will
be returned (according to PeeringDB).

Example:

```no-highlight
{% for missing in autonomous_system | missing_sessions(local_as) %}
IPv4: {{ missing.ipaddr4 }}
IPv6: {{ missing.ipaddr6 }}
{% endfor %}
```

## `prefix_list`

Fetches all the prefixes of an autonomous system or an IXP and returns them as
a JSON formatted object. For AS, prefixes are fetched using `bgpq3` (or
`bgpq4`) but can come from the local cache if present. For IXP, prefixes are
fetched from the PeeringDB local cache.

If the `family` parameter is set to `6` or `4` only the prefixes belonging to
the given family will be returned, as a list.

Example:

```no-highlight
{% set prefixes = autonomous_system | prefix_list %}
```

## `as_list`

Fetches the AS list of an autonomous system and returns it as a list of
integers. It is fetched using `bgpq3` (or `bgpq4`) but can come from the local
cache if present.

Example:

```no-highlight
{% set as_list = autonomous_system | as_list %}
```

## `connections`

On an IXP or a router, it will return all connections attached to it.

Example:

```no-highlight
{% for connection in router | connections %}
IPv4: {{ connection.ipv4_address }}
IPv6: {{ connection.ipv6_address }}
{% endfor %}
```

## `local_ips`

Applied on a session, the filter will fetch the local IP used to establish the
session. If applied on an IXP or a BGP group, it will return IP addresses (v4
and v6) configured for the IXP/BGP group. In any other case, it will give
back a null value. If `4` or `6` is passed as extra parameter, only the IPs
matching the version will be returned.

Examples:

```no-highlight
Local IPs: {{ session | local_ips }}
Local IPs: {{ ixp | local_ips }}
Local IPv6: {{ ixp | local_ips(6) }}
Local IPv4: {{ ixp | local_ips(4) }}
```

## `sessions` / `route_server`

When using `sessions` on a BGP group or an IXP, peering sessions setup in the
group or on the IXP will be returned as an iterable object. `route_server`
works similarly but will only give back sessions setup with route servers on
an IXP.

Examples:

```no-highlight
{% for session in ixp | sessions %}
{% for session in ixp | route_server(6) %}
```

## `direct_sessions` / `ixp_sessions`

When used on an autonomous system, it will return direct peering sessions or
respectively IXP peering sessions setup with the AS.

If family with a value of `4` or `6` is passed as extra parameter, only the
sessions with a IP version matching will be returned.

* If group is passed as extra parameter for `direct_sessions`, only the
  sessions contained in given group will be returned.
* If ixp is passed as extra parameter for `ixp_sessions`, only the sessions
  contained in given IXP will be returned.

Examples:

```no-highlight
{% for session in autonomous_system | direct_sessions %}
{% for session in autonomous_system | ixp_sessions(family=6) %}
{% for session in router | ixp_sessions(ixp=internet_exchange) %}
```

## `ip_version`

For a BGP session, it will return the IP version of the session given the IP
address field.

Example:

```no-highlight
{% if 6 == session | ip_version %}
```

## `max_prefix`

For a BGP session, it will return the max prefix value corresponding to the
remote AS and the IP address family.

Example:

```no-highlight
unicast {
    prefix-limit {
        maximum {{ session | max_prefix }};
    }
}
```

## `cisco_password`

From a valid Cisco type 7 password, returns the password stripping the magic
word prefix.

Example:

```no-highlight
{% if session.encrypted_password %}
password encrypted {{ session.encrypted_password | cisco_password }}
{% elif session.password %}
password clear {{ session.password }}
{% endif %}
```

## `direct_peers` / `ixp_peers`

For a router, fetches all peers connected to it. When using `direct_peers`
only peers with at least one direct peering session will be fetched while
`ixp_peers` will fetch peers with at least on peering session setup on an IXP
connected to the router.

Both filters can optionally take a slug value (as a string) to fetch sessions
from a specific BGP group or IXP.

Examples:

```no-highlight
{% for session in router | ixp_peers %}
...
{% for session in router | direct_peers('transit') %}
```

## `bfds`

For a router, fetches all BFD profiles used on this router.

Examples:

```no-highlight
{%- for bfd in router | bfds %}
...
{%- endfor %}
```

## `iter_export_policies` / `iter_import_policies`

Fetches routing policies applied on export or on import of an object. Note
that these filters will not traverse relationships, therefore, they will not
fetch AS policies for a session (for instance).

You can use a string as an option to these filters to select only a specific
field of the policies. Another optional argument named family can be used to
get policies only matching a given address family. Values for the family
parameter can be `4` or `6`.

Examples:

```no-highlight
export [ {{ session | iter_export_policies('slug') | join(' ') }} ];
import [ {{ session | iter_import_policies(field='slug', family=6) | join(' ') }} ];
```

## `merge_export_policies` / `merge_import_policies`

Merges all import or export routing policies from an object into a single
list. Policies are sorted based on their origin (AS/IXP/Session) and their
weight.

Note that a IXP policy is less preferred than an AS policy. Session policies
are the preferred ones. If a policy is referenced more than one time in the
policy list, only the most preferred occurence will be kept.

The keyword (as a string) `reverse` can be used as option to these two filters
to reverse the order of the list.

Examples:

```no-highlight
export [ {{ session | merge_export_policies | iterate('slug') | join(' ') }} ];
import [ {{ session | merge_import_policies('reverse') | iterate('slug') | join(' ') }} ];
```

## `routing_policies`

For a router, returns a list of all unique routing policies that need to be
configured on the router.

The returned list contains only unique policies, ordered by their name. This
is useful for generating the routing policy configuration section of a router.

You can use a string as an option to this filter to select only a specific
field of the policies. Another optional argument named `family` can be used to
get policies only matching a given address family. Values for the family
parameter can be `4` or `6`.

Examples:

```no-highlight
{% for policy in router | routing_policies %}
route-policy {{ policy.slug }}
  # {{ policy.name }}
  ...
end-policy
{% endfor %}

policies [ {{ router | routing_policies('slug') | join(' ') }} ];

{% for policy in router | routing_policies(family=6) %}
route-policy {{ policy.slug }}
  ...
end-policy
{% endfor %}
```

## `communities`

Fetches communities applied to an object.

You can use a string as an option to this filter to select only a specific
field of communities.

Examples:

```no-highlight
communities [ {{ session | communities('value') | join(' ') }} ];
communities [ {{ ixp | communities | join(' ') }} ];
```

## `merge_communities`

Merges all communities from an object into a single list. For BGP session,
group's, router's and autonomous system's communities will be merged together, avoiding
duplicates.

Example:

```no-highlight
communities [ {{ session | merge_communities | iterate('value') | join(' ') }} ];
```

## `contact`

Get the first matching contact for an autonomous system, an IXP or a BGP
session. A role name (case insensitive) must be given as parameter. An
optional `field` parameter can be given to only return the value of said
field.

Contacts found in PeeringDB are not included in the potential matches list.

Examples:

```no-highlight
{{ session | contact('technical') }}
{{ session.autonomous_system | contact('technical', field='name') }}
```

## `context_has_key` / `context_has_not_key`

Checks if the config context of an object contains a given key.
`context_has_not_key` filter is the exact opposite of `context_has_key`. The
filters' behaviour can be tweaked with the `recursive` argument. The default
value for `recursive` is `True` which means that the key will be searched in
nested hashes. It won't be if `recursive` is set to `False`.

Examples:

```no-highlight
{% if session | context_has_key('local_asn') %}
{% if ixp | context_has_not_key('ignore') %}
{% if router | context_has_key('region', recursive=False) %}
```

## `context_get_key`

Retrieves the value of a key in an object's config context. If the key is not
found, a default null value will be returned. The default value can be changed
by setting the `default` parameter of the filter. The filter will search
through nested hashes, but this can be disabled by setting the `recursive`
parameter to `False`.

Examples:

```no-highlight
{{ session | context_get_key('local_asn') }}
{{ ixp | context_get_key('ignore', default=False) }}
{{ if router | context_get_key('region', recursive=False) }}
```

## `as_json` / `as_yaml`

Convert an object or a list of objects (database result) as JSON or YAML. Keys
sorting can be disabled by setting the `sort_keys` parameter to `False`.
Indentation can be changed by setting the `indent` parameter to a positive
numeric value (default is 4 for JSON and 2 for YAML).

Examples:

```no-highlight
{{ router | connections | as_json }}
{{ router | connections | as_yaml }}

{% for connection in router | connections %}
{{ connection | as_yaml }}
{% endfor %}
```

## `indent`

Appends `n` chars to the beginning of each line of a value which is parsed as
a string. Remove the chars before applying the indentation if `reset` is set
to `True`.

```no-highlight
{% for ixp in dataset %}
{{ ixp.slug }}:
{{ ixp | prefix_list | as_yaml | indent(2) }}
{% endfor %}
```
