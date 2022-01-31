# Cisco IOS template from tutorial

```
{#- Generic IOS Template #}
{#- We define the type of template for reference #}
{%- set template_type="cisco-ios"%}
{#- To avoid conflict with prefedined elements,
we prepend everything we define#}
{%- set p="pm-"%}
!
! Communitiy Lists
!
!
{#- Generate named lists for all communities #}
{#- also generate delete list for incoming communities #}
{%- for community in communities %}
ip community-list standard {{p}}{{community.slug}}-{{community.type}} permit {{community.value}}
ip community-list standard {{p}}comm-delete permit {{community.value}}
{%-endfor%}
!
!
{#- AS Configuration: Do this for all ASes known #}
{%- for as in autonomous_systems %}
  {%- for tag in as.tags.all() if tag.slug == "filter-prefixes" and as.prefixes %}
{#- If you want prefix filtering for an as, apply a tag  #}
!
! Prefix-lists for AS{{as.asn}} - {{as.name}}
!
    {%- for thisprefix in as.prefixes.ipv4 %}
ip prefix-list {{p}}from-as{{as.asn}} permit {{thisprefix.prefix}}
      {%- if not thisprefix.exact %} le {{thisprefix['less-equal']}}{%-endif%}
    {%- endfor %}
!
    {%- for thisprefix in as.prefixes.ipv6 %}
ipv6 prefix-list {{p}}from-as{{as.asn}} permit {{thisprefix.prefix}}
      {%- if not thisprefix.exact %} le {{thisprefix['less-equal']}}{%-endif%}
    {%- endfor %}
!
  {%-else%}
{#- Delete old set if still exists #}
no ip prefix-list {{p}}from-as{{as.asn}}
no ipv6 prefix-list {{p}}from-as{{as.asn}}
ip prefix-list {{p}}from-as{{as.asn}} permit 0.0.0.0/0 le 32
ipv6 prefix-list {{p}}from-as{{as.asn}} permit ::0/0 le 128
!
  {%-endfor%}
  {#- Generate Community Lists #}
  {%- for community in as.communities.all() %}
    {%- if community.type == "ingress" %}
  	  {%- for tag in community.tags.all() %}
  	    {%- if tag.slug == "normal-community" %}
ip community-list standard {{p}}reg-communities-as{{ as.asn }}-in permit {{ community.value }}
        {%- endif %}
      {%- endfor %}
    {%- endif %}
  {%- endfor %}
  {%- for community in as.communities.all() %}
    {%- if community.type == "egress" %}
      {%- for tag in community.tags.all() %}
        {%- if tag.slug == "normal-community" %}
ip community-list standard {{p}}reg-communities-as{{ as.asn }}-out permit {{ community.value }}
        {%- endif %}
      {%- endfor %}
    {%- endif %}
  {%- endfor %}
{%-endfor %}
!
! IXP Peering sessions
!
{#- Work on Policies #}
!
! IXP policies
!
{%- for ixp in internet_exchange_points %}
  {%- for session in ixp |  sessions %}
    {%- if session.enabled %}
! Session with AS{{session.autonomous_system.asn}} ID:{{ session.id }} at {{ixp.name}}
! Put "deny" clause at the end
route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in deny 65535
! Delete all our own communities incoming at the beginning
route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in permit 1
  set comm-list {{p}}comm-delete delete
  continue
!
! Then set all required communities for this IXP using continue
route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in permit 2
      {%-for community in ixp.communities.all() %}
        {%-if community.type == "ingress"%}
  set community {{community.value}} additive
        {%-endif%}
      {%-endfor%}
  continue
! Then put all the rest "flattened" into clauses
! In: {{session | merge_import_policies |  iterate('slug') | join(',') }}
      {%-for policy in session | merge_import_policies%}
        {%-set outer=loop.index%}
        {%- if policy.config_context is iterable %}
          {%- for part in policy.config_context %}
            {%- if part == template_type%}
              {%- for statement in policy.config_context[part] %}
route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in {{statement.result}} {{outer*1000+loop.index}}
                {%-for inner in statement.match%}
  match {{inner}}
                {%-endfor%}
                {%-for inner in statement.set%}
  set {{inner}}
                {%-endfor%}
              {%-endfor%}
            {%-endif%}
          {%-endfor%}
        {%-endif%}
      {%-endfor%}
!
! End of IN
!
! Same for Out: "deny" clause at the end
route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out deny 65535
! Set communities at the beginning
route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out permit 1
      {%-for community in ixp.communities.all() %}
        {%-if community.type == "egress"%}
  set community {{community.value}} additive
        {%-endif%}
      {%-endfor%}
  continue
!
      {%-for policy in session | merge_export_policies%}
! And all the export policies
! Out: {{session | merge_export_policies |  iterate('slug') | join(',') }}

        {%-set outer=loop.index%}
        {%- if policy.config_context is iterable %}
          {%- for part in policy.config_context %}
            {%- if part == template_type%}
              {%- for statement in policy.config_context[part] %}
route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out {{statement.result}} {{outer*1000+loop.index}}
                {%-for inner in statement.match%}
  match {{inner}}
                {%-endfor%}
                {%-for inner in statement.set%}
  set {{inner}}
                {%-endfor%}
              {%-endfor%}
            {%-endif%}
          {%-endfor%}
        {%-endif%}
      {%-endfor%}
    {%-endif%}
  {%-endfor%}
{%-endfor%}
{#- We iterate again inside the BGP configuration. Only 'enabled' sessions are configure
   Currenly IPv4 and IPv6 are treated equally
#}
!
router bgp {{ local_as.asn }}
  no bgp enforce-first-as
{%- for ixp in internet_exchange_points %}
  {%- for session in ixp |  sessions %}
    {%- if session.enabled %}
    ! AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name | safe_string }}
    neighbor {{ session | ip }} remote-as {{ session.autonomous_system.asn }}
    neighbor {{ session | ip }} description {{ session.autonomous_system.name | safe_string }}
        {%- if session.encrypted_password %}
    neighbor {{ session | ip }} password encrypted {{ session.encrypted_password | cisco_password }}
        {%- elif session.password %}
    neighbor {{ session | ip }} password clear {{ session.password }}
        {%- endif %}
    address-family ipv{{ session | ip_version }} unicast
      neighbor {{ session | ip }} activate
      neighbor {{ session | ip }} route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in in
      neighbor {{ session | ip }} route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out out
      neighbor {{ session | ip }} prefix-list {{p}}from-as{{session.autonomous_system.asn}} in
      neighbor {{ session | ip }} send-community both
      neighbor {{ session | ip }} remove-private-as
        {%- if session | max_prefix %}
      neighbor {{ session | ip }} maximum-prefix {{ session | max_prefix }} 95
        {%- endif %}
    exit-address-family
    {%- else %}
   no neighbor {{ session | ip }}
    {%-endif%}
  {%-endfor%}
{%-endfor%}
{#- We iterate through all sessions first and generate the policies #}
{#- In case someone forgets to apply policies, the generic policies from the
start of this file are used
#}
! Direct Peering Sessions
!
router bgp {{ local_as.asn }}
  no bgp enforce-first-as
  no bgp default ipv4-unicast
{%- for as in autonomous_systems %}
  {%- for session in as | direct_sessions %}
    {%- if session.enabled %}
  ! AS{{ session.autonomous_system.asn }} - {{ session.autonomous_system.name | safe_string }}
  neighbor {{ session | ip }} remote-as {{ session.autonomous_system.asn }}
  neighbor {{ session | ip }} description {{ session.autonomous_system.name | safe_string }}
      {%- if session.encrypted_password %}
  neighbor {{ session | ip }} password encrypted {{ session.encrypted_password | cisco_password }}
      {%- elif session.password %}
  neighbor {{ session | ip }} password clear {{ session.password }}
      {%- endif %}
  address-family ipv{{ session | ip_version }} unicast
    neighbor {{ session | ip }} activate
    neighbor {{ session | ip }} route-map {{p}}{{session.relationship}}-out out
    neighbor {{ session | ip }} route-map {{p}}{{session.relationship}}-in in
    neighbor {{ session | ip }} prefix-list {{p}}from-as{{as.asn}} in
    neighbor {{ session | ip }} send-community both
    neighbor {{ session | ip }} remove-private-as
      {%- if session | max_prefix %}
    neighbor {{ session | ip }} maximum-prefix {{ session | max_prefix }} 95
      {%- endif %}
  exit-address-family
    {%- else %}
   no neighbor {{ session | ip }}
    {%-endif%}
  {%-endfor%}
{%-endfor%}
end
```
