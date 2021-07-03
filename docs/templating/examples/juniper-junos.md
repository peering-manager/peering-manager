# Juniper Junos

```no-highlight
protocols {
    bgp {
{%- for ixp in internet_exchange_points %}
  {%- for family in (6, 4) %}
        replace: group ipv{{ family }}-{{ ixp.slug }} {
            type external;
            multipath;
            advertise-inactive;
    {%- if ixp | iter_import_policies %}
            import [ {{ ixp | iter_import_policies('slug') | join(' ') }} ];
    {%- endif %}
            family inet{% if family == 6 %}6{% endif %} {
                unicast;
            }
    {%- if ixp | iter_export_policies %}
            export [ {{ ixp | iter_export_policies('slug') | join(' ') }} ];
    {%- endif %}
    {%- for session in ixp | sessions(family) %}
            neighbor {{ session.ip_address }} {
      {%- if not session.enabled %}
                disable;
      {%- endif %}
                description "Peering: AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name }}";
      {%- if family == 6 and session.autonomous_system.ipv6_max_prefixes > 0 %}
                family inet6 {
                    unicast {
                        prefix-limit {
                            maximum {{ session.autonomous_system.ipv6_max_prefixes }};
                        }
                    }
                }
      {%- endif %}
      {%- if family == 4 and session.autonomous_system.ipv4_max_prefixes > 0 %}
                family inet {
                    unicast {
                        prefix-limit {
                            maximum {{ session.autonomous_system.ipv4_max_prefixes }};
                        }
                    }
                }
      {%- endif %}
      {%- if session | iter_import_policies %}
                import [ {{ session | iter_import_policies('slug') | join(' ') }} ];
      {%- endif %}
      {%- if session | iter_export_policies %}
                export [ {{ session | iter_export_policies('slug') | join(' ') }} ];
      {%- endif %}
      {%- if session.encrypted_password %}
                authentication-key "{{ session.encrypted_password }}";
      {%- elif session.password %}
                authentication-key "{{ session.password }}";
      {%- endif %}
                peer-as {{ session.autonomous_system.asn }};
            }
    {%- endfor %}
        }
  {%- endfor %}
{%- endfor %}

{%- for group in bgp_groups %}
  {%- for family in (6, 4) %}
        replace: group ipv{{ family }}-{{ group.slug }} {
            type external;
            multipath;
            advertise-inactive;
    {%- if group | iter_import_policies %}
            import [ {{ group | iter_import_policies('slug') | join(' ') }} ];
    {%- endif %}
            family inet{% if family == 6 %}6{% endif %} {
                unicast;
            }
    {%- if group | iter_export_policies %}
            export [ {{ group | iter_export_policies('slug') | join(' ') }} ];
    {%- endif %}
    {%- for session in group | sessions(family) | filter(router=router) %}
            neighbor {{ session.ip_address }} {
      {%- if not session.enabled %}
                disable;
      {%- endif %}
                description "Peering: AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name }}";
      {%- if family == 6 and session.autonomous_system.ipv6_max_prefixes > 0 %}
                family inet6 {
                    unicast {
                        prefix-limit {
                            maximum {{ session.autonomous_system.ipv6_max_prefixes }};
                        }
                    }
                }
      {%- endif %}
      {%- if family == 4 and session.autonomous_system.ipv4_max_prefixes > 0 %}
                family inet {
                    unicast {
                        prefix-limit {
                            maximum {{ session.autonomous_system.ipv4_max_prefixes }};
                        }
                    }
                }
      {%- endif %}
      {%- if session | iter_import_policies %}
                import [ {{ session | iter_import_policies('slug') | join(' ') }} ];
      {%- endif %}
      {%- if session | iter_export_policies %}
                export [ {{ session | iter_export_policies('slug') | join(' ') }} ];
      {%- endif %}
      {%- if session.encrypted_password %}
                authentication-key "{{ session.encrypted_password }}";
      {%- elif session.password %}
                authentication-key "{{ session.password }}";
      {%- endif %}
                peer-as {{ session.autonomous_system.asn }};
            }
    {%- endfor %}
        }
  {%- endfor %}
{%- endfor %}
    }
}
policy-options {
{%- for c in communities %}
    community {{ c.name }} members {{ c.value }};
{%- endfor %}
}
```
