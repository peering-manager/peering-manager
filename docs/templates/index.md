# Templating

Peering Manager comes with a built-in templating feature. This feature can be
used to generate the BGP configuration of routers to peer on Internet Exchange
points but also with direct peering sessions that can be grouped together.

!!! warning
    If you use the template feature inside each Internet Exchange, you should
    move it to templates defined per-router. The original feature per-IX will
    be removed in a near future.

## Jinja2

The templating feature is based on [Jinja2](http://jinja.pocoo.org/docs/2.9/).
Defined templates just have to follow the Jinja2 syntax and Peering Manager
will take care of everything else.

## Configuration Template

The following variables are provided to generate a configuration based on a
template:

  * `my_asn` exposing the ASN specified in the configuration (your ASN)
  * `bgp_groups` exposing details about direct peering sessions in groups
  * `internet_exchange` exposing details about the current IX
  * `routing_policies` containing the list of routing policies
  * `communities` containing the list of communities

It is possible to iterate over these variables, except the first one, using the
`for` keyword of Jinja2. More details can be found about how to use these in
the examples below.

### Functions And Filters

Peering Manager exposes custom functions and filters that can be used in Jinja2
based templates.

`prefix_list` will fetch the list of prefixes given two parameters: an
Autonomous System number and an address family (IP version). The ASN must be a
valid integer (e.g. 201281), the address family must be an integer as well (4
means IPv4, 6 means IPv6, any other values means both families). Here is an
example that could be used in a template for JUNOS:

```no-highlight
policy-options {
    {%- for group in peering_groups %}
    {%- for asn in group.peers %}
    prefix-list ipv{{ group.ip_version }}-as{{ asn }} {
        {%- for p in prefix_list(asn, group.ip_version) %}
        {{ p.prefix }};
        {%- endfor %}
    }
    {%- endfor %}
    {%- endfor %}
}
```

## Example

Template examples are provided for:

  * [Juniper JUNOS](juniper-junos.md)
  * [Cisco IOS-XR](cisco-iosxr.md)
  * [Arista EOS](arista-eos.md)
