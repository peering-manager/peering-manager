# Arista EOS

```no-highlight
router bgp {{ local_as.asn }}
{%- for internet_exchange in internet_exchanges %}
  {%- for family in (6, 4) %}
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ family }} peer-group
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ family }} next-hop-self
   address-family ipv{{ family }}
    {%- if internet_exchange | merge_import_policies %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ family }} route-map {{ session | merge_import_policies }} in
    {%- else %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ family }} route-map reject-all in
    {%- endif %}
    {%- if internet_exchange | merge_export_policies %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ family }} route-map {{ session | merge_export_policies }} out
    {%- else %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ family }} route-map reject-all out
    {%- endif %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ family }} activate
   !
  {%- endfor %}
  {%- for session in internet_exchange | sessions %}
   neighbor {{ session.ip_address }} peer-group peer-ixp-{{ internet_exchange.slug }}-v{{ session | ip_version }}
   neighbor {{ session.ip_address }} remote-as {{ session.autonomous_system.asn }}
   neighbor {{ session.ip_address }} description "Peering: AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name }}"
    {%- if session | max_prefix %}
   neighbor {{ session.ip_address }} maximum-routes {{ session | max_prefix }}
    {%- endif %}
    {%- if session.is_route_server %}
   no neighbor {{ session.ip_address }} enforce-first-as
    {%- endif %}
    {%- if session.encrypted_password %}
   neighbor {{ session.ip_address }} password {{ session.encrypted_password }}
    {%- elif session.password %}
   neighbor {{ session.ip_address }} password 0 {{ session.password }}
    {%- endif %}
    {%- if session.enabled %}
   no neighbor {{ session.ip_address }} shutdown
    {%- else %}
   neighbor {{ session.ip_address }} shutdown
    {%- endif %}
   address-family ipv{{ session | ip_version }}
    {%- if session | merge_import_policies %}
      neighbor {{ session.ip_address }} route-map {{ session | merge_import_policies }} in
    {%- endif %}
    {%- if session | merge_export_policies %}
      neighbor {{ session.ip_address }} route-map {{ session | merge_export_policies }} out
    {%- endif %}
   !
  {%- endfor %}
{%- endfor %}
exit
```
