# Cisco IOS-XR

```no-highlight
router bgp {{ local_as.asn }}
{%- for ixp in internet_exchange_points %}
  {%- for session in ixp | sessions %}}
    {%- if session.enabled %}
   neighbor {{ session.ip_address }}
   remote-as {{ session.autonomous_system.asn }}
   description {{ session.autonomous_system.name | safe_string }}
      {%- if session.encrypted_password %}
   password encrypted {{ session.encrypted_password | cisco_password }}
      {%- elif session.password %}
   password clear {{ session.password }}
      {%- endif %}
      {%- if session.is_route_server %}
   use neighbor-group ng{{ session | ip_version }}-ROUTESRV
      {%- else %}
   use neighbor-group ng{{ session | ip_version }}-PEERING
      {%- endif %}
   address-family ipv{{ session | ip_version }} unicast
      {%- if session | iter_import_policies %}
   route-policy {{ session | iter_import_policies('slug') | join(' ') }} in
      {%- endif %}
      {%- if session | iter_export_policies %}
   route-policy {{ session | iter_export_policies('slug') | join(' ') }} out
      {%- endif %}
      {%- if session | max_prefix %}
   maximum-prefix {{ session | max_prefix }} 95 restart 15
      {%- endif %}
    {%- else %}
   no neighbor {{ session.ip_address }}
    {%- endif %}
  {%- endfor %}
{%- endfor %}
```
