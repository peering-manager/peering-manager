# Templating

Peering Manager comes with a built-in templating feature. This feature can be
used to generate configuration based on peering sessions recorded for each
Internet exchange points.

## Jinja2

The templating feature is based on [Jinja2](http://jinja.pocoo.org/docs/2.9/).
Defined templates just have to follow the Jinja2 syntax and Peering Manager
will take care of everything else.

## Configuration Template

Configuration templates are generated using 3 main variables:

  * internet_exchange
  * peering_groups
  * communities

The `internet_exchange` variable has several fields:

  * `name` is the name of the IX
  * `slug` is the name of the IX in a configuration friendly format
  * `ipv6_address` is the IPv6 address used to peer
  * `ipv4_address` is the IPv4 address used to peer

The `peering_groups` variable is a list of 2 elements, one for IPv6 sessions
and the other for IPv4. It is possible to iterate over this variable.

Each group have a name and sessions:

  * `name` is a string equals to **ipv6** or **ipv4**
  * `sessions` is a list of peering sessions, it is possible to iterate over
    this list. Each object of this list corresponds to one peering session,
    with the following properties:
    * `peer_as` is the remote ASN
    * `peer_as_name` is the name of the remote AS
    * `ip_version` is the IP version (can be 6 or 4)
    * `ip_address` is the IP address of the remote AS
    * `max_prefixes` is the maximum prefix-limit

The `communities` variable is an iteratable list, each item is a dictionary
containing two elements: the `name` and the `value` of the community. If no
communities are listed of the Internet exchange, this list will be empty.

## Example

This template is an example that can be used for Juniper devices.
```
protocols {
    bgp {
        {%- for group in peering_groups %}
        group {{ group.name }}-{{ internet_exchange.slug }} {
            type external;
            multipath;
            {%- for session in group.sessions %}
            neighbor {{ session.ip_address }} {
                description "Peering: AS{{ session.peer_as }} - {{ session.peer_as_name }}";
                {%- if session.max_prefixes > 0 %}
                {%- if session.ip_version == 6 %}
                family inet6 {
                {%- else %}
                family inet {
                {%- endif %}
                    unicast {
                        prefix-limit {
                            maximum {{ session.max_prefixes }};
                        }
                    }
                }
                {%- endif %}
                peer-as {{ session.peer_as }};
            }
            {%- endfor %}
        }
        {%- endfor %}
    }
}
```
