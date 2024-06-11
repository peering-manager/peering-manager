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
    {%- for session in router | ixp_sessions(family=family, ixp=ixp) %}
            {%- if not session.enabled %}inactive: {%- endif %}
            neighbor {{ session | ip }} {
      {%- if not session.enabled %}{#- Junos>=19.1 #}
                shutdown;
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
    {%- for session in router | direct_sessions(family=family, group=group)  %}
            {%- if not session.enabled %}inactive: {%- endif %}
            neighbor {{ session | ip }} {
      {%- if not session.enabled %}{#- Junos>=19.1 #}
                shutdown;
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
{#- Build route-filter-lists for each peer ASN  #}
{%- for as in autonomous_systems %}
{%- for tag in as.tags.all() if tag.slug == "filter-prefixes" and as.prefixes %}
{#- If you want prefix filtering for an as, apply a tag  #}
replace:
    route-filter-list AS{{as.asn}} {
{%- for prefix in as.prefixes.ipv4 %}
     {{ prefix.prefix }} {%- if not prefix.exact %} upto {{prefix['less-equal']}}{%-endif%}; 
{%-endfor %}
    }
replace:
    route-filter-list AS{{as.asn}}-INET6 {
{%- for prefix in as.prefixes.ipv6 %}
     {{ prefix.prefix }} {%- if not prefix.exact %} upto {{prefix['less-equal']}}{%-endif%};  
{%-endfor %}
    }
{%-endfor %}
{%-endfor %}
{%- for c in communities %}
    community {{ c.name }} members {{ c.value }};
{%- endfor %}
}
```

Notes:

- when using `if not session.enabled`, either `inactive:` (older releases) or
  `shutdown` (since 19.1, [link][shutdown]) can be used.

[shutdown]: https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/ref/statement/protocols-bgp-shutdown.html
