```no-hilight
{#- Build policy list #}
{%- macro policy_list(policies, address_family) %}[ {{ policies | selectattr('address_family', 'in', [0, address_family]) | map(attribute='slug') | join(' ') }} ]{%- endmacro %}

{#- Builds BGP Group #}
{%- macro build_bgp_group(group, group_name, address_family, max_prefixes=100) %}
{%- if group.deleted %}
        delete: group {{group_name}};
{%- else %}
        replace: group {{group_name}} {
            type external;
    {%- if group.import_routing_policies.all %}    
            import {{ policy_list(group.import_routing_policies, address_family) }};
    {%-  else %}
            import block-all;            
    {%- endif %}            
    {%- if group.export_routing_policies.all %}    
            export {{ policy_list(group.export_routing_policies, address_family) }};
    {%-  else %}
            export block-all;            
    {%- endif %}            
            family {% if address_family == 6 %}inet6{% else %}inet{% endif %} {
                unicast {
                    prefix-limit {
                        maximum: {{max_prefixes}};
                        teardown 90 idle-timeout 120;
                    }
                }
            }
        }
{%- endif%}
{%- endmacro %}

{#- Generate description for BGP session #}
{%- macro session_description(session) -%}"{{ session.autonomous_system.name.encode('ascii', 'xmlcharrefreplace').decode() | replace('\"', '') }}{% if session.autonomous_system.contact_email %} - {{ session.autonomous_system.contact_name.encode('ascii', 'xmlcharrefreplace').decode() | replace('\"', '') }} ({{session.autonomous_system.contact_email.encode('ascii', 'xmlcharrefreplace').decode() | replace('\"', '') }}){% endif %}"{%- endmacro -%}

{#- Build BGP Session for a BGP group #}
{%- macro build_session(group, group_name, address_family, session, default_max_prefixes=100) %}
{%- if not group.deleted and not session.deleted %}
        group {{group_name}} {
            {% if session.enabled %}replace:{% else %}inactive:{% endif %} neighbor {{ session.ip_address }} {
                description "{{session_description(session)}}";
    {%- set import_policies = group.import_routing_policies + session.autonomous_system.import_routing_policies +  session.import_routing_policies %}
    {%- if import_policies %}
                import { policy_list(import_routing_policies, address_family) }};
    {%- endif %}
    {%- set export_policies = group.export_routing_policies + session.autonomous_system.export_routing_policies +  session.export_routing_policies %}
    {%- if export_policies %}
                export { policy_list(export_routing_policies, address_family) }};
    {%- endif %}
    {%- if session.password %}
        {%- if session.encrypted_password %}
                authentication-key "{{ session.encrypted_password }}";
        {%- else %}
                authentication-key "{{ session.password }}";
        {%- endif %}
    {%- endif %}
    {%- if session.multihop_ttl > 1 %}
                multihop {
                    ttl {{session.multihop_ttl}};
                }
    {%- endif %}
                peer-as {{ session.autonomous_system.asn }};
            }            
        }
{%- endif %}
{%- endmacro %}


{%- macro build_communities() %}
{%- for community in communities %}
    {%- if community.deleted %}
    delete: community {{ community.slug }};
    {%- else %}
    community {{ community.slug }} members {{ community.value }};
    {%- endif %}
{%- endfor %}
{%- endmacro %}

{%- macro build_policies() %}
{%- for policy in routing_policies %}
    {%- if policy.deleted %}
    delete: policy-statement {{ policy.slug }};
    {%- else %}
{#- Put your own policies here, or manage it some other way #}
    replace: policy-statement {{ policy.slug }} {
        term stub {
            then next policy;
        }        
    }
    {%- endif %}
{%- endfor %}
{%- endmacro %}

policy-options {
    {{- build_communities() }}
    {{- build_policies() }}
}
protocols {
    bgp {
{%- for internet_exchange in internet_exchanges | sort(attribute='name') %}
    {%- for address_family, sessions in internet_exchange.sessions.items() | sort %}
        {%- set group_name = "ix-%s-v%d" | format(internet_exchange.slug, address_family) %}
        {{- build_bgp_group(internet_exchange, group_name, address_family) }}
        {%- for session in sessions | sort(attribute='ip_address') %}
            {{- build_session(internet_exchange, group_name, address_family, session) }}
        {%- endfor %}
    {%- endfor %}
{%- endfor %}
{%- for bgp_group in bgp_groups %}
    {%- for address_family, sessions in bgp_group.sessions.items() | sort %}
        {%- set group_name = "%s-v%d" | format(bgp_group.slug, address_family) %}
        {{- build_bgp_group(bgp_group, group_name, address_family) }}
        {%- for session in sessions %}
                {{- build_session(bgp_group, group_name, address_family, session) }}
        {%- endfor %}   
    {%- endfor %}
{%- endfor %}
    }
}
```
