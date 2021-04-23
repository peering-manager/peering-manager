```no-highlight
protocols {
    bgp {
        {%- for ixp in internet_exchanges %}
        {%- for family, sessions in ixp.sessions() %}
        replace: group ipv{{ family }}-{{ ixp.slug }} {
            type external;
            multipath;
            advertise-inactive;
            {%- if ixp.import_policies() %}
            import [ {{ ixp | iter_import_policies('slug') | join(' ') }} ];
            {%- endif %}
            family inet{% if family == 6 %}6{% endif %} {
                unicast;
            }
            {%- if ixp.export_policies() %}
            export [ {{ ixp | iter_export_policies('slug') | join(' ') }} ];
            {%- endif %}
            {%- for session in sessions %}
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
                {%- if session.import_policies() %}
                import [ {{ session | iter_import_policies('slug') | join(' ') }} ];
                {%- endif %}
                {%- if session.export_policies() %}
                export [ {{ session | iter_export_policies('slug') | join(' ') }} ];
                {%- endif %}
                {%- if session.password %}
                {%- if session.encrypted_password %}
                authentication-key "{{ session.encrypted_password }}";
                {%- else %}
                authentication-key "{{ session.password }}";
                {%- endif %}
                {%- endif %}
                peer-as {{ session.autonomous_system.asn }};
            }
            {%- endfor %}
        }
        {%- endfor %}
        {%- endfor %}

        {%- for group in bgp_groups %}
        {%- for family, sessions in group.sessions() %}
        replace: group ipv{{ family }}-{{ group.slug }} {
            type external;
            multipath;
            advertise-inactive;
            {%- if group.import_policies() %}
            import [ {{ group | iter_import_policies('slug') | join(' ') }} ];
            {%- endif %}
            family inet{% if family == 6 %}6{% endif %} {
                unicast;
            }
            {%- if group.export_policies() %}
            export [ {{ group | iter_export_policies('slug') | join(' ') }} ];
            {%- endif %}
            {%- for session in sessions %}
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
                {%- if session.import_routing_policies %}
                import [ {{ session | iter_import_policies('slug') | join(' ') }} ];
                {%- endif %}
                {%- if session.export_routing_policies %}
                export [ {{ session | iter_export_policies('slug') | join(' ') }} ];
                {%- endif %}
                {%- if session.password %}
                {%- if session.encrypted_password %}
                authentication-key "{{ session.encrypted_password }}";
                {%- else %}
                authentication-key "{{ session.password }}";
                {%- endif %}
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
