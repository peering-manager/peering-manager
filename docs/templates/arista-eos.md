```no-highlight
router bgp {{ my_asn }}
        {%- for internet_exchange in internet_exchanges %}
        {%- for address_family, sessions in internet_exchange.sessions.items() %}
        {%- if sessions|length > 0 %}
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} peer-group
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} next-hop-self
   {% if address_family == 6 -%}
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} maximum-routes 10
   {%- else -%}
   neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} maximum-routes 100
   {%- endif -%}
      {%- if address_family == 6 %}
   address-family ipv6
      {%- endif %}
      {%- if internet_exchange.import_routing_policies %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} route-map {% for import_policy in internet_exchange.import_routing_policies %}{%- if import_policy.address_family == address_family %}{{ import_policy.slug }} {% endif %}{% endfor %}in
      {%- else %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} route-map block-all in
      {%- endif %}
      {%- if internet_exchange.export_routing_policies %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} route-map {% for export_policy in internet_exchange.export_routing_policies %}{%- if export_policy.address_family == address_family %}{{ export_policy.slug }} {% endif %}{% endfor %}out
      {%- else %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} route-map block-all out
      {%- endif %}
      {%- if address_family == 6 %}
      neighbor peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }} activate
      {%- endif %}
   !
   {%- for session in sessions %}
    neighbor {{ session.ip_address }} peer-group peer-ixp-{{ internet_exchange.slug }}-v{{ address_family }}
    neighbor {{ session.ip_address }} remote-as {{ session.autonomous_system.asn }}
    neighbor {{ session.ip_address }} description "{{ session.autonomous_system.name }}"
    {%- if address_family == 6 and session.autonomous_system.ipv6_max_prefixes > 0 %}
    neighbor {{ session.ip_address }} maximum-routes {{ session.autonomous_system.ipv6_max_prefixes }}
    {%- endif %}
    {%- if address_family == 4 and session.autonomous_system.ipv4_max_prefixes > 0 %}
    neighbor {{ session.ip_address }} maximum-routes {{ session.autonomous_system.ipv4_max_prefixes }}
    {%- endif %}

    {%- if session.is_route_server %}
    no neighbor {{ session.ip_address }} enforce-first-as
    {%- endif %}
    {%- if session.password %}
    {%- if session.encrypted_password %}
    neighbor {{ session.ip_address }} password 7 {{ session.encrypted_password }}
    {%- else %}
    neighbor {{ session.ip_address }} password 0 {{ session.password }}
    {%- endif %}
    {%- endif %}
    {%- if not session.enabled %}
    neighbor {{ session.ip_address }} shutdown
    {%- else %}
    no neighbor {{ session.ip_address }} shutdown
    {%- endif %}
    {%- if session.import_routing_policies %}
    {%- if address_family == 6 %}
    address-family ipv6
    {%- endif %}
       neighbor {{ session.ip_address }} route-map {% for import_policy in session.import_routing_policies %}{%- if (import_policy.address_family == address_family or export_policy.address_family == 0) %}{{ import_policy.slug }} {% endif %}{% endfor %}in
    {%- endif %}
    {%- if session.export_routing_policies %}
       neighbor {{ session.ip_address }} route-map {% for export_policy in session.export_routing_policies %}{%- if (export_policy.address_family == address_family or export_policy.address_family == 0) %}{{ export_policy.slug }} {% endif %}{% endfor %}out
    {%- endif %}
    !
{%- endfor %}
        {%- endif %}
        {%- endfor %}
        {%- endfor %}
exit
```
