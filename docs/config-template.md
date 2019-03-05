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

  * `internet_exchange`
  * `peering_groups`
  * `communities`

The `internet_exchange` variable has several fields:

  * `name` is the name of the IX
  * `slug` is the name of the IX in a configuration friendly format
  * `ipv6_address` is the IPv6 address used to peer
  * `ipv4_address` is the IPv4 address used to peer
  * `export_routing_policies` is the routing policy list used for exporting
    routes, each element of the list has a `name` and `slug` attribute
  * `import_routing_policies` is the routing policy list used for importing
    routes, each element of the list has a `name` and `slug` attribute

The `peering_groups` variable is a list of 2 elements, one for IPv6 sessions
and the other for IPv4. It is possible to iterate over this variable.

Each group have a name and sessions:

  * `ip_version` is a integer equals to `6` or `4`
  * `peers` is a dictionary containing inner dictionaries. It is possible to
    iterate over the main dictionary using the `items()` function in the Jinja2
    template like `{%- for asn, details in group.peers.items() %}`. Each inner
    is then identified with an AS number and contains several variables
    describing the peer (AS) and its sessions:
    * `as_name` is the name of the remote AS
    * `max_prefixes` is the maximum prefix-limit for the current IP version
    * `sessions` is a list of dictionaries, each dictionary has values
      identified by the following keys: `ip_address`, `is_route_server`
      `enabled`, `password`, `export_routing_policies` and
      `import_routing_policies`.
      The value for the `ip_address` key is a string representing the IP
      address. The value for the for `is_route_server` key tells if
      the session is setup with a route server (true) or not (false). The value
      for the `password` is the password that you specified as a string. Please
      not that there is no processing of any kind for the password. If you
      stored it as clear text, it will be returned back to the template as
      clear text too. The value for the for `enabled` key tells if the session
      is enabled (true) or not (false). The values for the
      `export_routing_policies` and `import_routing_policies` are the routing
      policy objects associated with the session, the `slug` fields of these
      objects are probably the only relevant fields to be used in the template

The `communities` variable is an iterable list, each item is a dictionary
containing two elements: the `name` and the `value` of the community. If no
communities are listed for the Internet exchange, this list will be empty.

## Example

### JunOS

This template is an example that can be used for Juniper devices.
```no-highlight
protocols {
    bgp {
        {%- for group in peering_groups %}
        replace: group ipv{{ group.ip_version }}-{{ internet_exchange.slug }} {
            type external;
            multipath;
            advertise-inactive;
            {%- if import_routing_policies|length > 0 %}
            import [ {{ import_routing_policies | map(attribute='slug') | join(' ') }} ];
            {%- else %}
            import import-all;
            {%- endif %}
            family {% if group.ip_version == 6 %}inet6{% else %}inet{% endif %} {
                unicast;
            }
            {%- if export_routing_policies|length > 0 %}
            export [ {{ export_routing_policies | map(attribute='slug') | join(' ') }} ];
            {%- else %}
            export export-all;
            {%- endif %}
            {%- for asn, details in group.peers.items() %}
            {%- for session in details.sessions %}
            {% if not session.enabled %}inactive: {% endif %}neighbor {{ session.ip_address }} {
                description "Peering: AS{{ asn }} - {{ details.as_name }}";
                {%- if details.max_prefixes > 0 %}
                {%- if group.ip_version == 6 %}
                family inet6 {
                {%- else %}
                family inet {
                {%- endif %}
                    unicast {
                        prefix-limit {
                            {%- if group.ip_version == 6 %}
                            maximum {{ details.max_prefixes }};
                            {%- else %}
                            maximum {{ details.max_prefixes }};
                            {%- endif %}
                        }
                    }
                }
                {%- endif %}
                {%- if session.import_routing_policies|length > 0 %}
                import [ {{ session.import_routing_policies | map(attribute='slug') | join(' ') }} ];
                {%- endif %}
                {%- if session.export_routing_policies|length > 0 %}
                export [ {{ session.export_routing_policies | map(attribute='slug') | join(' ') }} ];
                {%- endif %}
                {%- if session.password %}
                authentication-key "{{ session.password }}";
                {%- endif %}
                peer-as {{ asn }};
            }
            {%- endfor %}
            {%- endfor %}
        }
        {%- endfor %}
    }
}
```

### IOS-XR

This template is an example that can be used for Cisco IOS-XR devices.
```no-highlight
!
router bgp 12345
 vrf internet
  {%- for group in peering_groups %}
  {%- for asn, details in group.peers.items() %}
  {%- for session in details.sessions %}
  neighbor {{ session.ip_address }}
   {%- if not session.enabled %}
   shutdown
   {%- elif session.enabled %}
   no shutdown
   {%- endif %}
   remote-as {{ asn }}
{#- Seattle #}
   {%- if 'ixp-six' == internet_exchange.slug %}
   use neighbor-group IXP-SIX-V{{ group.ip_version }}
   {%- elif 'ixp-equinix-sea' == internet_exchange.slug %}
   use neighbor-group IXP-EQUINIX-SEA-V{{ group.ip_version }}
{#- New York #}
   {%- elif 'ixp-nyiix' == internet_exchange.slug %}
   use neighbor-group IXP-NYIIX-V{{ group.ip_version }}
   {%- elif 'ixp-decix-ny' == internet_exchange.slug %}
   use neighbor-group IXP-DECIX-NY-V{{ group.ip_version }}
   {%- elif 'ixp-drix-ny' == internet_exchange.slug %}
   use neighbor-group IXP-DRIX-NY-V{{ group.ip_version }}
{#- Montreal -#}
   {%- elif 'ixp-qix' == internet_exchange.slug %}
   use neighbor-group IXP-QIX-V{{ group.ip_version }}
{#- Toronto -#}
   {%- elif 'ixp-torix' == internet_exchange.slug %}
   use neighbor-group IXP-TORIX-V{{ group.ip_version }}
   {%- endif %}
   {%- if session.password %}
   password {{ session.password }}
   {%- endif %}
   description "AS{{ asn }} - {{ details.as_name }}"
   address-family {% if group.ip_version == 4 %}ipv4{% else %}ipv6{% endif %} unicast
    maximum-prefix {{ details.max_prefixes }} 100 restart 60
   !
  !
 {%- endfor %}
 {%- endfor %}
 {%- endfor %}
 !
!
```

### Arista EOS
This template is an example that can be used for Arista EOS devices.

```no-highlight
router bgp 8757
   {%- for group in peering_groups %}
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} peer-group
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} next-hop-self
   {% if group.ip_version == 6 -%}
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} maximum-routes 10
   {%- else -%}
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} maximum-routes 100
   {%- endif -%}    
      {%- if group.ip_version == 6 %}
   address-family ipv6
      {%- endif %}
      {%- if import_routing_policies|length > 0 %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} route-map {{ import_routing_policies | map(attribute='slug') | join(' ') }} in
      {%- else %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} route-map block-all in
      {%- endif %}
      {%- if export_routing_policies|length > 0 %}  
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} route-map {{ export_routing_policies | map(attribute='slug') | join(' ') }} out
      {%- else %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} route-map block-all out
      {%- endif %}
      {%- if group.ip_version == 6 %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} activate
      {%- endif %}
   !
   {%- for asn, details in group.peers.items() %}
   {%- for session in details.sessions %}
    neighbor {{ session.ip_address }} peer-group peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }}
    neighbor {{ session.ip_address }} remote-as {{ asn }}
    neighbor {{ session.ip_address }} description "{{ details.as_name }}"
    neighbor {{ session.ip_address }} maximum-routes {{ details.max_prefixes }}
    {%- if session.is_route_server == true %}
    no neighbor {{ session.ip_address }} enforce-first-as
    {%- endif %}
    {%- if session.password %}
    neighbor {{ session.ip_address }} password 0 {{ session.password }}
    {%- endif %}
    {%- if not session.enabled %}
    neighbor {{ session.ip_address }} shutdown
    {%- endif %}
    {%- if session.import_routing_policies|length > 0 %}
    {%- if group.ip_version == 6 %}
    address-family ipv6
    {%- endif %}
       neighbor {{ session.ip_address }} route-map {{ session.import_routing_policies | map(attribute='slug') | join(' ') }} in
    {%- endif %}
    {%- if session.export_routing_policies|length > 0 %}
       neighbor {{ session.ip_address }} route-map {{ session.export_routing_policies | map(attribute='slug') | join(' ') }} out
    {%- endif %}
    !
  {%- endfor %}
  {%- endfor %}
  {%- endfor %}
exit
```
