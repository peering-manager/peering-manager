# VyOS template as used by AS200249

This is a template as used by [AS200249](https://www.peeringdb.com/net/31954) where (in addition to the usual BGP configuration) route maps are created using tags to always route traffic to the best IX based on distance/latency.

```
{%- set local_pref_map = {
'frankfurt': 200,
'amsterdam': 125,
'prague': 125,
'berlin': 125,
'default': 100
} -%}
{%- set cities = ['frankfurt', 'amsterdam', 'prague', 'berlin'] -%}
{%- set tags = ['peer-source-frankfurt', 'peer-source-amsterdam', 'peer-source-prague', 'peer-source-berlin'] -%}
{%- set asns = { 'frankfurt': [], 'amsterdam': [], 'prague': [], 'berlin': [] } -%}
{%- set sessions = { 'frankfurt': [], 'amsterdam': [], 'prague': [], 'berlin': [] } -%}
{%- for as in autonomous_systems -%}
{%- for tag in as.tags.all() -%}
{%- if tag.slug in tags and as.prefixes -%}
{%- set city = tag.slug.split('-')[-1] -%}
{%- if city in asns -%}
{%- set _ = asns[city].append(as) -%}
{%- endif -%}
{%- endif -%}
{%- endfor -%}
{%- endfor -%}

{%- for city in cities -%}
{%- set rule_start = 10 -%}
{%- for as in asns[city] -%}
set policy as-path-list PEERS-{{ city | upper }} rule {{ rule_start + loop.index0 }} action permit
set policy as-path-list PEERS-{{ city | upper }} rule {{ rule_start + loop.index0 }} description "Peer {{ as.name }} |{{ city | capitalize }}"
set policy as-path-list PEERS-{{ city | upper }} rule {{ rule_start + loop.index0 }} regex "200249 {{ as.asn }}"
{% endfor %}
{%- endfor -%}
{%- for internet_exchange in internet_exchange_points -%}
{%- for session in internet_exchange | sessions -%}
{%- for tag in session.tags.all() -%}
{%- set city = tag.slug.split('-')[-1] -%}
{%- if city in sessions -%}
{%- set _ = sessions[city].append(session) -%}
{%- endif -%}
{%- endfor -%}
{%- endfor -%}
{%- endfor -%}


{%- for city in cities -%}
{%- set slug_value = 'peers-' ~ city -%}
{%- set community = communities.filter(slug=slug_value).first() -%}
{%- if community is not none -%}
{%- set community_values = community.value.split(',') -%}
{%- endif -%}
{%- set rule_start = 10 -%}
set policy route-map PEERS-{{ city | upper }}-v6 rule {{ rule_start + loop.index0 }} action permit
set policy route-map PEERS-{{ city | upper }}-v6 rule {{ rule_start + loop.index0 }} set local-preference {{ local_pref_map.get(location, local_pref_map[city]) }}
{%- set rule_counter = rule_start + loop.index0 -%}
{% for community in community_values %}
set policy route-map PEERS-{{ city | upper }}-v6 rule {{ rule_counter }} set large-community add {{ community }}
{%- endfor %}
set policy route-map PEERS-{{ city | upper }}-v6 rule {{ rule_start + loop.index0 }} set large-community add 200249:100:{{ local_pref_map.get(location, local_pref_map[city]) }}
{% endfor -%}

{%- for city in cities -%}
{%- set slug_value = 'peers-' ~ city -%}
{%- set community = communities.filter(slug=slug_value).first() -%}
{%- if community is not none -%}
{%- set community_values = community.value.split(',') -%}
{%- endif -%}
{%- set rule_start = 10 -%}
set policy route-map PEERS-{{ city | upper }}-v4 rule {{ rule_start + loop.index0 }} action permit
set policy route-map PEERS-{{ city | upper }}-v4 rule {{ rule_start + loop.index0 }} set local-preference {{ local_pref_map.get(location, local_pref_map[city]) }}
{%- set rule_counter = rule_start + loop.index0 -%}
{% for community in community_values %}
set policy route-map PEERS-{{ city | upper }}-v4 rule {{ rule_counter }} set large-community add {{ community }}
{%- endfor %}
set policy route-map PEERS-{{ city | upper }}-v4 rule {{ rule_start + loop.index0 }} set large-community add 200249:100:{{local_pref_map.get(location, local_pref_map[city]) }}
{% endfor %}
{%- set rule_start = namespace(c = 10) -%}
{%- set v4_count = namespace(c = 0) -%}
{%- set v6_count = namespace(c = 0) -%}
{%- for city in cities -%}
{%- for session in sessions[city] -%}
{%- if session | ip_version == 4 -%}
set policy route-map eBGP-import-v4 rule {{ rule_start.c + v4_count.c }} action permit
set policy route-map eBGP-import-v4 rule {{ rule_start.c + v4_count.c }} description '{{ session.autonomous_system.name |
safe_string }} | {{ city | capitalize }}'
set policy route-map eBGP-import-v4 rule {{ rule_start.c + v4_count.c }} match peer {{ session | ip }}
set policy route-map eBGP-import-v4 rule {{ rule_start.c + v4_count.c }} call PEERS-{{ city | upper }}-v4
{% set v4_count.c = v4_count.c + 1 %}
{%- endif -%}
{%- endfor -%}
{%- endfor -%}
set policy route-map eBGP-import-v4 rule 999 action permit
set policy route-map eBGP-import-v4 rule 999 description 'Set default local-pref'
set policy route-map eBGP-import-v4 rule 999 set local-preference 100
{% set rule_start = namespace(c = 10) -%}
{%- set v4_count = namespace(c = 0) -%}
{%- set v6_count = namespace(c = 0) -%}
{%- for city in cities -%}
{%- for session in sessions[city] -%}
{%- if session | ip_version == 6 -%}
set policy route-map eBGP-import-v6 rule {{ rule_start.c + v6_count.c }} action permit
set policy route-map eBGP-import-v6 rule {{ rule_start.c + v6_count.c }} description '{{ session.autonomous_system.name
|
safe_string }} | {{ city | capitalize }}'
set policy route-map eBGP-import-v6 rule {{ rule_start.c + v6_count.c }} match peer {{ session | ip }}
set policy route-map eBGP-import-v6 rule {{ rule_start.c + v6_count.c }} call PEERS-{{ city | upper }}-v6
{% set v6_count.c = v6_count.c + 1 %}
{%- endif -%}
{%- endfor -%}
{%- endfor -%}
set policy route-map eBGP-import-v6 rule 999 action permit
set policy route-map eBGP-import-v6 rule 999 description 'Set default local-pref'
set policy route-map eBGP-import-v6 rule 999 set local-preference 100


{% for internet_exchange in internet_exchange_points -%}
{%- for family in (6, 4) -%}
set protocols bgp peer-group ixp-{{ internet_exchange.slug }}-v{{ family }} local-as 200249
set protocols bgp peer-group ixp-{{ internet_exchange.slug }}-v{{ family }} description "IXP {{ internet_exchange.name }}"
set protocols bgp peer-group ixp-{{ internet_exchange.slug }}-v{{ family }} address-family ipv{{ family }}-unicast remove-private-as
{%- if internet_exchange | merge_import_policies %}
set protocols bgp peer-group ixp-{{ internet_exchange.slug }}-v{{ family }} address-family ipv{{ family }}-unicast route-map import {{ internet_exchange | iter_import_policies(family=family, field='slug') | join(' ') }}
{%- endif %}
{%- if internet_exchange | merge_export_policies %}
set protocols bgp peer-group ixp-{{ internet_exchange.slug }}-v{{ family }} address-family ipv{{ family }}-unicast route-map export {{ internet_exchange | iter_export_policies(family=family, field='slug') | join(' ') }}
{% endif -%}
{%-  endfor -%}
{%- for session in internet_exchange | sessions -%}
{%- if session.enabled or session.provisioning and not session.is_route_server %}
set protocols bgp neighbor {{ session | ip }} peer-group ixp-{{ internet_exchange.slug }}-v{{ session | ip_version}}
set protocols bgp neighbor {{ session | ip }} remote-as {{ session.autonomous_system.asn }}
set protocols bgp neighbor {{ session | ip }} description "AS{{ session.autonomous_system.asn }}:{{ session.autonomous_system.name | safe_string }}"
{%- if session | max_prefix %}
set protocols bgp neighbor {{ session | ip }} address-family ipv{{ session | ip_version }}-unicast maximum-prefix {{session | max_prefix }}
{%- endif %}
{%- endif -%}
{%- endfor -%}
{% endfor %}
{%- for group in bgp_groups %}
    {%- for family in (6, 4) %}
set protocols bgp peer-group {{ group.name }}-v{{ family }} local-as 200249

{%- if group | iter_import_policies %}
set protocols bgp peer-group {{ group.name }}-v{{ family }} address-family ipv{{ family }}-unicast route-map import {{
group | iter_import_policies(family=family, field='slug') | join(' ') }}
{%- endif %}
{%- if group | iter_export_policies %}
set protocols bgp peer-group {{ group.name }}-v{{ family }} address-family ipv{{ family }}-unicast route-map export {{
group | iter_export_policies(family=family, field='slug') | join(' ') }}
{%- endif %}
set protocols bgp peer-group {{ group.name }}-v{{ family }} address-family ipv{{ family }}-unicast soft-reconfiguration inbound
set protocols bgp peer-group {{ group.name }}-v{{ family }} address-family ipv{{ family }}-unicast remove-private-as

{%- for session in router | direct_sessions(family=family, group=group) -%}
set protocols bgp neighbor {{ session | ip }} peer-group {{ group.name }}-v{{ family }}
set protocols bgp neighbor {{ session | ip }} description "Transit: AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name }}"
{%- endfor %}
    {%- endfor %}
{%- endfor %}
```

## More information

For more information about configuring and use of the template, please look [here](https://bontekoe.technology/using-peering-manager-for-automated-configuration-on-vyos/)
