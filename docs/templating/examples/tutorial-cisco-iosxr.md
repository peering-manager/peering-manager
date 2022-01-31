# Cisco IOS XR template from tutorial

```
{#- Generic IOS XR Template #}
{#- We define the type of template for reference #}
{%- set template_type="cisco-iosxr"%}
{#- To avoid conflict with prefedined elements, we prefix everything we define#}
{%- set p="pm-"%}
{#- transit-provider, private-peering, customer #}
{#- we use private community 65500: for everything #}
!
! Communitiy Lists
!
{#- Generate named lists for all communities #}
{%- for community in communities %}
!
community-set {{p}}{{community.slug}}-{{community.type}}
  {{community.value}}
end-set
{%-endfor%}
community-set {{p}}comm-delete
{%- for community in communities %}
  {{community.value}}{%- if not loop.last%},{%-endif%}
{%-endfor%}
end-set
!
! Prefix lists
!
{%- for as in autonomous_systems %}
  {%- for tag in as.tags.all() if tag.slug == "filter-prefixes" and as.prefixes %}
  {#- If you want prefix filtering for an as, apply a tag  #}
!
! Prefix-list for AS{{as.asn}} - {{as.name}}
!
prefix-set {{p}}from-as{{as.asn}}
  # AS{{as.asn}} - {{as.name}}
    {%- for thisprefix in as.prefixes.ipv4+as.prefixes.ipv6 %}
      {{thisprefix.prefix}}
      {%- if not thisprefix.exact %} le {{thisprefix['less-equal']}}{%-endif%}
      {%- if not loop.last%},{%-endif%}
    {%- endfor %}
end-set
!
route-policy {{p}}prefixes-from-as{{as.asn}}
  # AS{{as.asn}} - {{as.name}}
  if destination in {{p}}from-as{{as.asn}} then
    pass
  else
    drop
  endif
end-policy
!
    {%-else%}
{#- Delete old set if still exists #}
no prefix-set {{p}}from-as{{as.asn}}
{#- Generate an empty policy if no filtering is wanted so the reference still works #}
route-policy {{p}}prefixes-from-as{{as.asn}}
  pass
end-policy
!
  {%-endfor %}
{%-endfor%}
!
! Configured Policies
!
{%- for policy in routing_policies %}
!
route-policy {{p}}{{policy.name}}
  {%- if policy.config_context is iterable %}
    {%- for part in policy.config_context %}
      {%- if part == template_type%}
        {%- for statement in policy.config_context[part] %}
 {#- Simply dump all statements one after another#}
 {{statement}}
        {%-endfor%}
      {%-endif%}
    {%-endfor%}
  {%-endif%}
end-policy
{%-endfor%}
!
{%- for as in autonomous_systems %}
!
! Route Policies for  AS{{as.asn}}
!
{#- Here the order of statements is important - adding communities is last so they do not get removed by a policy #}
route-policy {{p}}as-{{as.asn}}-in
  # {{as.name}}
  apply {{p}}prefixes-from-as{{as.asn}}
  {%- for policy in as | iter_import_policies()%}
  apply {{p}}{{policy.name}}
  {%-endfor%}
  {%-for community in as.communities.all()%}
    {%- if community.type == "ingress" %}
  set community {{p}}{{community.slug}}-{{community.type}} additive
    {%-endif%}
  {%-endfor%}
  pass
end-policy
!
route-policy {{p}}as-{{as.asn}}-out
  # {{as.name}}
{%- for policy in as | iter_export_policies()%}
  apply {{p}}{{policy.name}}
{%-endfor%}
{%-for community in as.communities.all()%}
  {%- if community.type == "egress" %}
set community {{p}}{{community.slug}}-{{community.type}} additive
  {%-endif%}
{%-endfor%}
  pass
end-policy
!
{%- endfor %}
{%- for ixp in internet_exchange_points %}
!
! Route Policies for IXP {{ixp.name}}
!
route-policy {{p}}ix-{{ixp.slug}}-in
 # {{ixp.name}}
 {%- for policy in ixp | iter_import_policies()%}
 apply {{p}}{{policy.name}}
 {%-endfor%}
 {%-for community in ixp.communities.all()%}
   {%- if community.type == "ingress" %}
 set community {{p}}{{community.slug}}-{{community.type}} additive
   {%-endif%}
 {%-endfor%}
 pass
end-policy
!
route-policy {{p}}ix-{{ixp.slug}}-out
 # {{ixp.name}}
 {%- for policy in ixp | iter_export_policies()%}
 apply {{p}}{{policy.name}}
 {%-endfor%}
 {%-for community in ixp.communities.all()%}
  {%- if community.type == "egress" %}
 set community {{p}}{{community.slug}}-{{community.type}} additive
  {%-endif%}
 {%-endfor%}
 pass
end-policy
!
{%-endfor%}
!
! IXP Session Policies
!
{%- for ixp in internet_exchange_points %}
  {%- for session in ixp | sessions %}
    {%- if session.enabled %}
! Session with AS{{session.autonomous_system.asn}} ID:{{ session.id }} at {{ixp.name}}
route-policy {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in
  # {{session.autonomous_system.name}}
  apply {{p}}ix-{{ixp.slug}}-in
  apply {{p}}as-{{session.autonomous_system.asn}}-in
  {%- for policy in session | iter_import_policies()%}
  apply {{p}}{{policy.name}}
  {%-endfor%}
end-policy
!
route-policy {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out
  # {{session.autonomous_system.name}}
  apply {{p}}ix-{{ixp.slug}}-out
  apply {{p}}as-{{session.autonomous_system.asn}}-out
  {%- for policy in session | iter_export_policies()%}
  apply {{p}}{{policy.name}}
  {%-endfor%}
end-policy
!
    {%-else%}
    {#- Session is disabled, remove route policy as well #}
no route-policy {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in
no route-policy {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out
    {%-endif%}
  {%-endfor%}
{%-endfor%}

router bgp {{ local_as.asn }}
  bgp enforce-first-as disable
{%- for ixp in internet_exchange_points %}
  {%- for session in ixp |  sessions %}
    {%- if session.enabled %}
  neighbor {{ session | ip }}
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
      route-policy {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in in
      route-policy {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out out
      send-extended-community-ebgp
      send-community-ebgp
      remove-private-AS
      {%- if session | max_prefix %}
      maximum-prefix {{ session | max_prefix }} 95
      {%- endif %}
    {%- else %}
   no neighbor {{ session | ip }}
    {%-endif%}
  {%-endfor%}
{%-endfor%}


```
