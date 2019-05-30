```no-highlight
protocols {
    bgp {
        {%- for internet_exchange in internet_exchanges %}
        {%- for address_family, sessions in internet_exchange.sessions.items() %}
        {%- if sessions|length > 0 %}
        replace: group ipv{{ address_family }}-{{ internet_exchange.slug }} {
            type external;
            multipath;
            advertise-inactive;
            {%- if internet_exchange.import_routing_policies %}
            import [ {{ internet_exchange.import_routing_policies | map(attribute='slug') | join(' ') }} ];
            {%- else %}
            import import-all;
            {%- endif %}
            family {% if address_family == 6 %}inet6{% else %}inet{% endif %} {
                unicast;
            }
            {%- if internet_exchange.export_routing_policies %}
            export [ {{ internet_exchange.export_routing_policies | map(attribute='slug') | join(' ') }} ];
            {%- else %}
            export export-all;
            {%- endif %}
            {%- for session in sessions %}
            {% if not session.enabled %}inactive: {% endif %}neighbor {{ session.ip_address }} {
                description "Peering: AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name }}";
                {%- if address_family == 6 and session.autonomous_system.ipv6_max_prefixes > 0 %}
                family inet6 {
                    unicast {
                        prefix-limit {
                            maximum {{ session.autonomous_system.ipv6_max_prefixes }};
                        }
                    }
                }
                {%- endif %}
                {%- if address_family == 4 and session.autonomous_system.ipv4_max_prefixes > 0 %}
                family inet {
                    unicast {
                        prefix-limit {
                            maximum {{ session.autonomous_system.ipv4_max_prefixes }};
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
                peer-as {{ session.autonomous_system.asn }};
            }
            {%- endfor %}
        }
        {%- endif %}
        {%- endfor %}
        {%- endfor %}

        {%- for bgp_group in bgp_groups %}
        {%- for address_family, sessions in bgp_group.sessions.items() %}
        {%- if sessions|length > 0 %}
        replace: group ipv{{ address_family }}-{{ bgp_group.slug }} {
            type external;
            multipath;
            advertise-inactive;
            {%- if bgp_group.import_routing_policies %}
            import [ {{ bgp_group.import_routing_policies | map(attribute='slug') | join(' ') }} ];
            {%- else %}
            import import-all;
            {%- endif %}
            family {% if address_family == 6 %}inet6{% else %}inet{% endif %} {
                unicast;
            }
            {%- if bgp_group.export_routing_policies %}
            export [ {{ bgp_group.export_routing_policies | map(attribute='slug') | join(' ') }} ];
            {%- else %}
            export export-all;
            {%- endif %}
            {%- for session in sessions %}
            {% if not session.enabled %}inactive: {% endif %}neighbor {{ session.ip_address }} {
                description "Peering: AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name }}";
                {%- if address_family == 6 and session.autonomous_system.ipv6_max_prefixes > 0 %}
                family inet6 {
                    unicast {
                        prefix-limit {
                            maximum {{ session.autonomous_system.ipv6_max_prefixes }};
                        }
                    }
                }
                {%- endif %}
                {%- if address_family == 4 and session.autonomous_system.ipv4_max_prefixes > 0 %}
                family inet {
                    unicast {
                        prefix-limit {
                            maximum {{ session.autonomous_system.ipv4_max_prefixes }};
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
                peer-as {{ session.autonomous_system.asn }};
            }
            {%- endfor %}
        }
        {%- endif %}
        {%- endfor %}
        {%- endfor %}
    }
}
policy-options {
    {%- for community in communities %}
    community {{ community.name }} members {{ community.value }};
    {%- endfor %}
}
```
