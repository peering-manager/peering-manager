```no-highlight
router bgp {{ my_as.asn }}
{%- for internet_exchange in internet_exchanges %}
{%- for address_family, sessions in internet_exchange.sessions.items() %}
{%- if sessions|length > 0 %}
{%- for session in sessions %}
{% if session.enabled %}
    neighbor {{ session.ip_address }}
      remote-as {{ session.autonomous_system.asn }}
      {%- if session.autonomous_system.irr_as_set %}
      description {{ session.autonomous_system.name }} ({{ session.autonomous_system.irr_as_set }})
      {%- else %}
      description {{ session.autonomous_system.name }}
      {%- endif %}
      {%- if session.password %}
      {%- if session.encrypted_password %}
      password encrypted {{ session.encrypted_password|replace("7 ","") }}
      {%- else %}
      password clear {{ session.password }}
      {%- endif %}
      {%- endif %}
      {%- if session.is_route_server %}
      use neighbor-group ng{{ address_family }}-ROUTESRV
      {%- else %}
      use neighbor-group ng{{ address_family }}-PEERING
      {%- endif %}
      address-family ipv{{ address_family }} unicast
      {%- if session.import_routing_policies %}
        route-policy {{ session.import_routing_policies | map(attribute='name') | join(' ') }} in
      {%- endif %}
      {%- if session.export_routing_policies %}
        route-policy {{ session.import_routing_policies | map(attribute='name') | join(' ') }} out
      {%- endif %}
      {%- if address_family == 4 and session.autonomous_system.ipv4_max_prefixes > 0 %}
        maximum-prefix {{ session.autonomous_system.ipv4_max_prefixes }} 95 restart 15
      {%- endif %}
      {%- if address_family == 6 and session.autonomous_system.ipv6_max_prefixes > 0 %}
        maximum-prefix {{ session.autonomous_system.ipv6_max_prefixes }} 95 restart 15
      {%- endif %}
{%- else %}
    no neighbor {{ session.ip_address }}
{%- endif %}
{%- endfor %}
{%- endif %}
{%- endfor %}
{%- endfor %}
```
