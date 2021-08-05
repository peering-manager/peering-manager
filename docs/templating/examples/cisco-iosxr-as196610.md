# Cisco IOS XR templated as used by AS196610
Since a few days [DE-CIX Academy](https://de-cix.net/academy)
[AS196610](https://peeringdb.com/asn/196610) is using Peering Manager in production
(well, it is a research network, so not much traffic). This is the template
being used. At placeholder you can find detailed explanations on the template.

```no-highlight
{#- Generic Policies for Relationships #}
{#- transit-provider, private-peering, customer #}
!
! Hard-Coded Policies for direct peerings
!
route-policy customer-in
  apply unwanted-routes
  set local-preference 10000
  delete large-community in my-communities
  set large-community ({{local_as.asn}}:1:47000) additive
  pass
end-policy
!
route-policy customer-out
  if destination in my-networks or large-community matches-any announce-to-customers then
    set med igp-cost
    pass
  else
    drop
  endif
end-policy
!
route-policy private-peering-in
  apply unwanted-routes
  delete large-community in my-communities
  set large-community ({{local_as.asn}}:0:21200) additive
  set large-community ({{local_as.asn}}:1:41000) additive
  set local-preference 1000
end-policy
!
route-policy private-peering-out
  if large-community matches-any announce-to-peering or destination in my-networks then
    set med 0
    pass
  else
    drop
  endif
end-policy
!
route-policy transit-provider-in
  if destination in default-routes then
    set local-preference 10
    delete large-community in my-communities
    set large-community ({{local_as.asn}}:1:40000) additive
    pass
  endif
  apply unwanted-routes
  set local-preference 10
  delete large-community in my-communities
  set large-community ({{local_as.asn}}:1:41000) additive
  pass
end-policy
!
route-policy transit-provider-out
  if destination in my-networks or large-community matches-any announce-to-upstream then
    set med igp-cost
    pass
  else
    drop
  endif
end-policy
!
{# All configured policies #}
{%- for policy in routing_policies %}
!
route-policy {{policy.name}}
{%- if policy.config_context is iterable %}
  {%- for statement in policy.config_context %}
 {#- Simply dump all statements one after another#}
 {{statement}}
  {%-endfor%}
{%-endif%}
end-policy
{%-endfor%}
!
{#- AS Configuration: Do this for all ASes known #}
{%- for as in autonomous_systems %}
{%- for tag in as.tags.all() if tag.slug == "filter-prefixes" and as.prefixes %}
{#- If you want prefix filtering for an as, apply a tag  #}
!
! Prefix-list for AS{{as.asn}}
!
prefix-set from-as{{as.asn}}
  # {{as.name}}
{%- for thisprefix in as.prefixes.ipv4+as.prefixes.ipv6 %}
  {{thisprefix.prefix}}
  {%- if not thisprefix.exact %} le {{thisprefix['less-equal']}}{%-endif%}
  {%- if not loop.last%},{%-endif%}
{%- endfor %}
end-set
!
route-policy prefixes-from-as{{as.asn}}
  # {{as.name}}
  if destination in from-as{{as.asn}} then
    pass
  else
    drop
  endif
end-policy
!
{%-else%}
{#- Delete old set if still exists #}
no prefix-set from-as{{as.asn}}
{#- Generate an empty policy if no filtering is wanted so the reference still works #}
route-policy prefixes-from-as{{as.asn}}
  pass
end-policy
!
{%-endfor %}
!
! Communities for AS{{as.asn}}
large-community-set large-communities-as{{ as.asn }}-in
  {%- for community in as.communities.all() %}
    {%- if community.type == "ingress" %}
      {%- for tag in community.tags.all() %}
        {%- if tag.slug == "large-community" %}
 {{ community.value }},
        {%- endif %}
      {%- endfor %}
    {%- endif %}
  {%- endfor %}
 {{local_as.asn}}:9999:9999
end-set
large-community-set large-communities-as{{ as.asn }}-out
  {%- for community in as.communities.all() %}
    {%- if community.type == "egress" %}
	    {%- for tag in community.tags.all() %}
	     {%- if tag.slug == "large-community" %}
 {{ community.value }},
       {%- endif %}
      {%- endfor %}
	  {%- endif %}
  {%- endfor %}
 {{local_as.asn}}:9999:9999
end-set
!
extcommunity-set rt ext-communities-as{{ as.asn }}-in
{%- for community in as.communities.all() %}
  {%- if community.type == "ingress" %}
    {%- set outer_loop_last = loop.last %}
	  {%- for tag in community.tags.all() %}
	    {%- if tag.slug == "extended-community" %}
        {{ community.value }}{%- if not outer_loop_last %},{%-endif %}
      {%- endif %}
    {%- endfor %}
	{%- endif %}
{%- endfor %}
end-set
extcommunity-set rt ext-communities-as{{ as.asn }}-out
{%- for community in as.communities.all() %}
  {%- if community.type == "egress" %}
    {%- set outer_loop_last = loop.last %}
	  {%- for tag in community.tags.all() %}
	    {%- if tag.slug == "extended-community" %}
        {{ community.value }}{%- if not outer_loop_last %},{%-endif %}
      {%- endif %}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
end-set
!
community-set reg-communities-as{{ as.asn }}-in
{%- for community in as.communities.all() %}
  {%- if community.type == "ingress" %}
    {%- set outer_loop_last = loop.last %}
	  {%- for tag in community.tags.all() %}
	    {%- if tag.slug == "normal-community" %}
        {{ community.value }}{%- if not outer_loop_last %},{%-endif %}
      {%- endif %}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
end-set
community-set reg-communities-as{{ as.asn }}-out
{%- for community in as.communities.all() %}
  {%- if community.type == "egress" %}
    {%- set outer_loop_last = loop.last %}
    {%- for tag in community.tags.all() %}
      {%- if tag.slug == "normal-community" %}
        {{ community.value }}{%- if not outer_loop_last %},{%-endif %}
      {%- endif %}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
end-set
!
! Route Policies for  AS{{as.asn}}
!
{#- Here the order of statements is important - adding communities is last so they do not get removed by a policy #}
route-policy as-{{as.asn}}-in
  # {{as.name}}
  apply prefixes-from-as{{as.asn}}
{%- for policy in as | iter_import_policies()%}
  apply {{policy.name}}
{%-endfor%}
  set large-community large-communities-as{{ as.asn }}-in additive
  set extcommunity rt ext-communities-as{{ as.asn }}-in additive
  set community reg-communities-as{{ as.asn }}-in additive
end-policy
!
route-policy as-{{as.asn}}-out
  # {{as.name}}
{%- for policy in as | iter_export_policies()%}
  apply {{policy.name}}
{%-endfor%}
  set large-community large-communities-as{{ as.asn }}-out additive
  set extcommunity rt ext-communities-as{{ as.asn }}-out additive
  set community reg-communities-as{{ as.asn }}-out additive
end-policy
!
{%- endfor %}
{#- IXP Configuration - iterate over all IXPs
  1. Generate community Lists
  2. Generate policies
#}
{%- for ixp in internet_exchange_points %}
!
! Communities for {{ixp.name}}
large-community-set large-communities-{{ ixp.slug }}-in
  {%- for community in ixp.communities.all() %}
    {%- if community.type == "ingress" %}
      {%- for tag in community.tags.all() %}
        {%- if tag.slug == "large-community" %}
 {{ community.value }},
        {%- endif %}
      {%- endfor %}
    {%- endif %}
  {%- endfor %}
 {{local_as.asn}}:9999:9999
end-set
large-community-set large-communities-{{ ixp.slug }}-out
  {%- for community in ixp.communities.all() %}
    {%- if community.type == "egress" %}
	    {%- for tag in community.tags.all() %}
	     {%- if tag.slug == "large-community" %}
 {{ community.value }},
       {%- endif %}
      {%- endfor %}
	  {%- endif %}
  {%- endfor %}
 {{local_as.asn}}:9999:9999
end-set
!
extcommunity-set rt ext-communities-{{ ixp.slug }}-in
{%- for community in ixp.communities.all() %}
  {%- if community.type == "ingress" %}
    {%- set outer_loop_last = loop.last %}
	  {%- for tag in community.tags.all() %}
	    {%- if tag.slug == "extended-community" %}
        {{ community.value }}{%- if not outer_loop_last %},{%-endif %}
      {%- endif %}
    {%- endfor %}
	{%- endif %}
{%- endfor %}
end-set
extcommunity-set rt ext-communities-{{ ixp.slug }}-out
{%- for community in ixp.communities.all() %}
  {%- if community.type == "egress" %}
    {%- set outer_loop_last = loop.last %}
	  {%- for tag in community.tags.all() %}
	    {%- if tag.slug == "extended-community" %}
        {{ community.value }}{%- if not outer_loop_last %},{%-endif %}
      {%- endif %}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
end-set
!
community-set reg-communities-{{ ixp.slug }}-in
{%- for community in ixp.communities.all() %}
  {%- if community.type == "ingress" %}
    {%- set outer_loop_last = loop.last %}
	  {%- for tag in community.tags.all() %}
	    {%- if tag.slug == "normal-community" %}
        {{ community.value }}{%- if not outer_loop_last %},{%-endif %}
      {%- endif %}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
end-set
community-set reg-communities-{{ ixp.slug }}-out
{%- for community in ixp.communities.all() %}
  {%- if community.type == "egress" %}
    {%- set outer_loop_last = loop.last %}
    {%- for tag in community.tags.all() %}
      {%- if tag.slug == "normal-community" %}
        {{ community.value }}{%- if not outer_loop_last %},{%-endif %}
      {%- endif %}
    {%- endfor %}
  {%- endif %}
{%- endfor %}
end-set
!
! Route Policies for {{ixp.name}}
!
route-policy ix-{{ixp.slug}}-in
 # {{ixp.name}}
 {%- for policy in ixp | iter_import_policies()%}
 apply {{policy.name}}
 {%-endfor%}
 set large-community large-communities-{{ ixp.slug }}-in additive
 set extcommunity rt ext-communities-{{ ixp.slug }}-in additive
 set community reg-communities-{{ ixp.slug }}-in additive
end-policy
!
route-policy ix-{{ixp.slug}}-out
 # {{ixp.name}}
{%- for policy in ixp | iter_export_policies()%}
 apply {{policy.name}}
{%-endfor%}
 set large-community large-communities-{{ ixp.slug }}-out additive
 set extcommunity rt ext-communities-{{ ixp.slug }}-out additive
 set community reg-communities-{{ ixp.slug }}-out additive
end-policy
!
{%-endfor%}
{#- IXP Session Configuration
  This iterates over the IXP first and then over all sessions at that IXP
  Here just policies are generated - they apply the previously generated
  AS-specific and IXP-specific Policies
  again, order of statements is important
#}
{%- for ixp in internet_exchange_points %}
  {%- for session in ixp | sessions %}
    {%- if session.enabled %}
! Session with AS{{session.autonomous_system.asn}} ID:{{ session.id }} at {{ixp.name}}
route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-in
  # {{session.autonomous_system.name}}
  apply unwanted-routes
  apply ix-{{ixp.slug}}-in
  apply as-{{session.autonomous_system.asn}}-in
  {%- for policy in session | iter_import_policies()%}
  apply {{policy.name}}
  {%-endfor%}
end-policy
!
route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-out
  # {{session.autonomous_system.name}}
  apply as-{{session.autonomous_system.asn}}-out
  apply ix-{{ixp.slug}}-out
  {%- for policy in session | iter_export_policies()%}
  apply {{policy.name}}
  {%-endfor%}
end-policy
!
    {%-else%}
    {#- Session is disabled, remove route policy as well #}
no route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-in
no route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-out
    {%-endif%}
  {%-endfor%}
{%-endfor%}
!
{#- We iterate again inside the BGP configuration. Only 'enabled' sessions are configure
   Currenly IPv4 and IPv6 are treated equally
#}
!
router bgp {{ local_as.asn }}
{%- for ixp in internet_exchange_points %}
  {%- for session in ixp |  sessions %}
    {%- if session.enabled %}
  neighbor {{ session.ip_address }}
     remote-as {{ session.autonomous_system.asn }}
     description {{ session.autonomous_system.name | safe_string }}
      {%- if session.encrypted_password %}
     password encrypted {{ session.encrypted_password | cisco_password }}
      {%- elif session.password %}
     password clear {{ session.password }}
      {%- endif %}
      {%-if session.is_route_server %}
     no enforce-first-as
      {%-else%}
     enforce-first-as
      {%-endif%}
     address-family ipv{{ session | ip_version }} unicast
      route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-in in
      route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-out out
      send-extended-community-ebgp
      send-community-ebgp
      remove-private-AS
      {%- if session | max_prefix %}
      maximum-prefix {{ session | max_prefix }} 95
      {%- endif %}
    {%- else %}
   no neighbor {{ session.ip_address }}
    {%-endif%}
  {%-endfor%}
{%-endfor%}
{#- We iterate through all sessions first and generate the policies #}
{#- In case someone forgets to apply policies, the generic policies from the
start of this file are used
#}
! Direct Peering Sessions
{%- for as in autonomous_systems %}
{%- for session in as | direct_sessions %}
  {%- if session.enabled %}
! Session with AS{{session.autonomous_system.asn}} ID:{{ session.id }} direct
route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-in
  # {{session.autonomous_system.name}}
  apply unwanted-routes
  apply {{session.relationship}}-in
  {%- for policy in session | iter_import_policies()%}
  apply {{policy.name}}
  apply as-{{session.autonomous_system.asn}}-in
  {%-endfor%}
end-policy
!
route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-out
  # {{session.autonomous_system.name}}
  apply as-{{session.autonomous_system.asn}}-out
  apply {{session.relationship}}-out
  {%- for policy in session | iter_export_policies()%}
  apply {{policy.name}}
  {%-endfor%}
end-policy
!
  {%-else%}
no route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-in
no route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-out
  {%-endif%}
{%-endfor%}
{%-endfor%}
!
router bgp {{ local_as.asn }}
{%- for as in autonomous_systems %}
  {%- for session in as | direct_sessions %}
    {%- if session.enabled %}
  neighbor {{ session.ip_address }}
     remote-as {{ session.autonomous_system.asn }}
     description {{ session.autonomous_system.name | safe_string }}
      {%- if session.encrypted_password %}
     password encrypted {{ session.encrypted_password | cisco_password }}
      {%- elif session.password %}
     password clear {{ session.password }}
      {%- endif %}
      {%-if session.is_route_server %}
     no enforce-first-as
      {%-else%}
     enforce-first-as
      {%-endif%}
     address-family ipv{{ session | ip_version }} unicast
      route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-in in
      route-policy session-as{{session.autonomous_system.asn}}-id{{session.id}}-out out
      send-extended-community-ebgp
      send-community-ebgp
      remove-private-AS
      {%- if session | max_prefix %}
      maximum-prefix {{ session | max_prefix }} 95
      {%- endif %}
    {%- else %}
   no neighbor {{ session.ip_address }}
    {%-endif%}
  {%endfor%}
{%-endfor%}
exit
```
