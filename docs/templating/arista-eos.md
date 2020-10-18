```no-hilight
{#- Build policy list #}
{%- macro policy_list(policies, address_family) %}{{ policies | selectattr('address_family', 'in', [0, address_family]) | map(attribute='slug') | join(' ') }}{%- endmacro %}

{# Builds a BGP group #}
{%- macro build_bgp_group(group, group_name, address_family, max_prefixes=100) %}
{%- if group.deleted %}
    address-family ipv{{address_family}}
        no neighbor {{group_name}}
    !
    no neighbor {{group_name}}
{%- else %}
    neighbor {{group_name}} peer group
    neighbor {{group_name}} next-hop-self
    neighbor {{group_name}} maximum-routes {{ max_prefixes | int}}
    !
    address-family ipv{{address_family}}
    {%- if group.import_routing_policies %}
        neighbor {{group_name}} route-map {{ policy_list(group.import_routing_policies) }} in
    {%- else %}
        neighbor {{group_name}} route-map block-all in
    {%- endif %}
    {%- if group.export_routing_policies %}
        neighbor {{group_name}} route-map {{ policy_list(group.export_routing_policies) }} out
    {%- else %}
        neighbor {{group_name}} route-map block-all out
    {%- endif %}
        neighbor {{group_name}} activate
   !
{%- endif %}
{%- endmacro %}

{#- Generate description for BGP session #}
{%- macro session_description(session) -%}"{{ session.autonomous_system.name.encode('ascii', 'xmlcharrefreplace').decode() | replace('\"', '') }}{% if session.autonomous_system.contact_email %} - {{ session.autonomous_system.contact_name.encode('ascii', 'xmlcharrefreplace').decode() | replace('\"', '') }} ({{session.autonomous_system.contact_email.encode('ascii', 'xmlcharrefreplace').decode() | replace('\"', '') }}){% endif %}"{%- endmacro -%}

{#- Build a BGP session for a BGP group #}
{%- macro build_session(group, group_name, address_family, session, default_max_prefixes=100) %}
{%- if group.deleted or session.deleted %}
    no neighbor {{session.ip_address}}
{%- else %}
    {%- set max_prefixes = session.autonomous_system.ipv6_max_prefixes if address_family == 6 else session.autonomous_system.ipv4_max_prefixes %}
    neighbor {{ session.ip_address }} peer group {{group_name}}
    neighbor {{ session.ip_address }} remote-as {{ session.autonomous_system.asn }}
    neighbor {{ session.ip_address }} description {{ session_description(session)}}
    neighbor {{ session.ip_address }} maximum-routes {{ [max_prefixes, default_max_prefixes] | max }}
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
    {%- set import_policies = session.autonomous_system.import_routing_policies + session.import_routing_policies %}
    {%- if import_policies %}
    address-family ipv{{address_family}}
       neighbor {{ session.ip_address }} route-map {{ policy_list(import_routing_policies) }} in
    {%- endif %}
    {%- set export_policies = session.autonomous_system.import_routing_policies + session.import_routing_policies %}
    {%- if export_routing_policies %}
       neighbor {{ session.ip_address }} route-map {{ policy_list(export_routing_policies) }} out
    {%- endif %}
    {%- if 'is_route_server' in session and session.is_route_server %}
    no neighbor {{ session.ip_address }} enforce-first-as
    {%- endif %}
    !
{%- endif %}
{%- endmacro %}

{#- Build/delete communities #}
{%- macro build_communities() %}
{%- for community in communities %}
    {%- if community.deleted %}
no ip community-list {{community.slug}}
    {%- else %}
ip community-list {{community.slug}} permit {{community.value}}
    {%- endif %}
{%- endfor %}
{%- endmacro %}

{#- Build/delete route-map policies #}
{%- macro build_route_maps() %}
{%- for policy in routing_policies %}
    {%- if policy.deleted %}
no route-map {{policy.slug}} 
    {%- else %}
{#- Put your own policies here, or manage it some other way #}
route-map {{policy.slug}} 
    exit
!
    {%- endif %}
{%- endfor %}
{%- endmacro %}

{#- Main Template #}}
{{- build_communities() }}
{{- build_route_maps() }}
router bgp {{ my_asn }}
    no bgp default ipv4-unicast
{%- for internet_exchange in internet_exchanges | sort(attribute='name') %}
    {%- for address_family, sessions in internet_exchange.sessions.items() | sort %}
        {%- set group_name = "ix-%s-v%d" | format(internet_exchange.slug, address_family) %}
        {{- build_bgp_group(internet_exchange, group_name, address_family) }}
        {%- for session in sessions %}
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
exit
```
