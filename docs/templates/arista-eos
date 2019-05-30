!!! warning
    This template example needs an update.

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
    {%- endif %}
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
