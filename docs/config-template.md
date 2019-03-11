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

  * `my_asn` exposing the ASN specified in the configuration (your ASN)
  * `internet_exchange` exposing details about the current IX
  * `peering_groups` containing the list of peering sessions to by IP version

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
            {%- if internet_exchange.import_routing_policies %}
            import [ {{ internet_exchange.import_routing_policies | map(attribute='slug') | join(' ') }} ];
            {%- else %}
            import import-all;
            {%- endif %}
            family {% if group.ip_version == 6 %}inet6{% else %}inet{% endif %} {
                unicast;
            }
            {%- if internet_exchange.export_routing_policies %}
            export [ {{ internet_exchange.export_routing_policies | map(attribute='slug') | join(' ') }} ];
            {%- else %}
            export export-all;
            {%- endif %}
            {%- for asn, details in group.peers.items() %}
            {%- for session in details.sessions %}
            {% if not session.enabled %}inactive: {% endif %}neighbor {{ session.ip_address }} {
                description "Peering: AS{{ asn }} - {{ details.name }}";
                {%- if group.ip_version == 6 and details.ipv6_max_prefixes > 0 %}
                family inet6 {
                    unicast {
                        prefix-limit {
                            maximum {{ details.ipv6_max_prefixes }};
                        }
                    }
                {%- endif %}
                {%- if group.ip_version == 4 and details.ipv4_max_prefixes > 0 %}
                family inet {
                    unicast {
                        prefix-limit {
                            maximum {{ details.ipv4_max_prefixes }};
                        }
                    }
                }
                {%- endif %}
                {%- if session.import_routing_policies %}
                import [ {{ session.import_routing_policies | map(attribute='slug') | join(' ') }} ];
                {%- endif %}
                {%- if session.export_routing_policies %}
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
    maximum-prefix {% if group.ip_version == 4 %}{{ details.ipv4_max_prefixes }}{% else %}{{ details.ipv6_max_prefixes }}{% endif %} 100 restart 60
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
router bgp 12345
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
      {%- if internet_exchange.import_routing_policies %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} route-map {{ internet_exchange.import_routing_policies | map(attribute='slug') | join(' ') }} in
      {%- else %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} route-map block-all in
      {%- endif %}
      {%- if internet_exchange.export_routing_policies %}  
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ group.ip_version }} route-map {{ internet_exchange.export_routing_policies | map(attribute='slug') | join(' ') }} out
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
    neighbor {{ session.ip_address }} description "{{ details.name }}"
    neighbor {{ session.ip_address }} maximum-routes {% if group.ip_version == 6 %}{{ details.ipv6_max_prefixes }}{% else %}{{ details.ipv4_max_prefixes }}
    {%- if session.is_route_server %}
    no neighbor {{ session.ip_address }} enforce-first-as
    {%- endif %}
    {%- if session.password %}
    neighbor {{ session.ip_address }} password 0 {{ session.password }}
    {%- endif %}
    {%- if not session.enabled %}
    neighbor {{ session.ip_address }} shutdown
    {%- endif %}
    {%- if session.import_routing_policies %}
    {%- if group.ip_version == 6 %}
    address-family ipv6
    {%- endif %}
       neighbor {{ session.ip_address }} route-map {{ session.import_routing_policies | map(attribute='slug') | join(' ') }} in
    {%- endif %}
    {%- if session.export_routing_policies %}
       neighbor {{ session.ip_address }} route-map {{ session.export_routing_policies | map(attribute='slug') | join(' ') }} out
    {%- endif %}
    !
  {%- endfor %}
  {%- endfor %}
  {%- endfor %}
exit
```
