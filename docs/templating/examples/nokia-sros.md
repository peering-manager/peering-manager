# Noia SROS MD CLI templated as used by Nokia 7750 Peering routers

This template has been created during rollout of Nokia 7750 peering routers and has been tested on software versie 23.10.X.
I have removed all AS specific code and made a generic template you can use as a starting point to automate the configuration generation of your Nokia router.
This template is not perfect and may need some changes to fit in your environment. If you have question, don't hesistate to contact me.

## Configurable Options

### Tags

#### ORIGIN-VALIDATION
This TAG can be set on a neighbor, IX or BGP group level. If set we enable Origin Validation for this neighbor or BGP Group.

#### ROUTER-POLICY
This TAG  can be set on a Policy. When set the policy is a router policy and uses the specific policy-variables from config context data from a router. The two variables can be set are comm-deny-to and comm-depref-to. These can be used to depref or deny routes on specific routers if this community is set on the router.

#### DONT-EXPORT
This TAG can be set on a Policy. It will note export the policy to the router and gives you the option to define a policy local on the router and use it in Peering Manager to set on a peer or group.

#### FILTER-PREFIXES-V4
This TAG can be set on an AS Number. It will mean we do Prefix Filtering for this AS number for all V4 prefixes and will generate the prefix lists and policies to enable this

#### FILTER-PREFIXES-V6
This TAG can be set on an AS Number. It will mean we do Prefix Filtering for this AS number for all V6 prefides and will generate the prefix lists and policies to enable this

### Config Context

The following default config context are used in these templates
- Routing Policy V4 IN:	    Routing Policy Defaults IPv4 Peers and Transits Import		
- Routing Policy V4 OUT:	Routing Policy Defaults IPv4 Peers and Transits Export		
- Routing Policy V6 IN:	    Routing Policy Defaults IPv6 Peers and Transits Import		
- Routing Policy V6 OUT:	Routing Policy Defaults IPv6 Peers and Transits Output
- Filter Transit ASN:       Filter out routes that contain transit ASN

In this Routing Policy IN (V4/V4) contexts we store the default local-preference and med settings.
```
{
    "policy-variables": {
        "local-preference": 100,
        "med": 0
        
    }
}
```

In this Routing Policy OUT (V4/V4) contexts we store the default med and asprepend settings (How many prepends we want to apply on outgoing advertisements)
```
{
    "policy-variables": {
        "asprepend": 0,
        "med": 0
    }
}
```

In Filter Transit ASN we have this settings:. as-path-filter is the reference to the filter we use to filter out TRANSIT ASN's in the AS-PATH.

```
{
    "policy-variables": {
        "as-path-filter": "LARGE-TRANSIT-ASNS"
    }
}
```

### Status

This is the explanation how we have implemented the status setting of a peer/group:

- Provisioning: Session is created but will not be provisioned to the router
- Enabled: Session will be fully operational to the router
- Disabled: Session will be provisioned with admin-state disable
- Pre-Maintenance: Session will be created and will be up, but will be created with low local pref and routes will be send with Graceful Shutdown communities (PEER-OUT-GSHUT / PEER-IN-GSHUT)
- Maintenance: Session will be created and will be up, but no routes will be sent (BGP-REJECT-IN/BGP-REJECT-OUT)
- Decommissioning/Decommissioned: Session will be deleted from the router in the next config deployment. This is always the first step to delete a peering session. After this has been done a peer can safely be deleted from peering maanger

All other statusses are not officially supported and will result in peering to be deleted if it was active or it won't get provisioned.

# Configuration templates
To make the template a bit more readable, I decided to split it up in different sub templates. Just create configuration templates for every code part in your peering manager installation with the exact same name as the header.


## Nokia SROS Main template

```
{#- Generic Nokia SROS Template #}
{#- Define the type of template for reference #}
{%- set template_type = "nokia-sros" %}
{#- Delete the config blocks and recreate them to ensure removed blocks are deleted #}
{%- set delete_config = true %}
{#- Prefix everything we define to avoid conflicts with predefined elements #}
{%- set p = "PMGR-" %}
{#- Set My AS Number #}
{%- set my_asn = "64496" %}
############### DEFAULT CONFIG TO BE ADDED ###############
{% include_configuration "GITHUB Nokia SROS Default config" %}

configure {
  router "Base" {
        {#- START OF BGP CONFIG #}
        bgp {
        
        {#- BGP GROUPS #}
          ############### BGP GROUPS ###############
        {%- include_configuration "GITHUB Nokia SROS Sub - BGP Groups" %}

        {#- BGP IXP NEIGHBOURS #}
          ############### BGP NEIGHBOURS ###############
        {%- include_configuration "GITHUB Nokia SROS Sub - BGP Neighbors" %}

        }
      }

      {#- ROUTING POLICY PART #}

      ############### ROUTING POLICY ###############
      policy-options {
        {#- ROUTING POLICY GENERIC #}
        ############### ROUTING POLICY GENERIC ###############
        {%- include_configuration "GITHUB Nokia SROS Sub - Route Policy" %}

        {#- COMMUNITIES #}
        ############### COMMUNITIES ###############
        {%- include_configuration "GITHUB Nokia SROS Sub - Route Policy Communities" %}

        {#- Prefix Lists#}
        ############### PREFIX LISTS###############
        {%- include_configuration "GITHUB Nokia SROS Sub - Route Policy Prefix Lists" %}
      }
    }
```
## Nokia SROS Default config

This is the section we can use to add default configuration. We use the Nokia apply-groups to have some default EBGP/V4/V6 configuration that is common for all our BGP peers.
This groups includes default deny policy for BGP / Prefix limits and some timer settings. You can change this to your own needs/desired defaults

Next to BGP config we have an apply group that can be used on external interfaces. This apply groups adds an ingress filter that only allows traffic from peers we have configurated directly to our external interfaces. 

We also created some default policies/communities that are used in other sub configuration templates. 
The PMG-PEER-IN/OUT-V4/V6 are the most important policies. This policy is applied to every neigbour as first policy in the list of possible policies. 
The best practice is to add your own filtering rules before entry 100 (Bogons etc).


```
configure {
    groups {
        group "EBGP" {
            router "Base" {
                bgp {
                    group "<.*>" {
                        keepalive 30
                        min-route-advertisement 1
                        aigp false
                        multipath-eligible true
                        hold-time {
                            seconds 90
                            minimum-hold-time 90
                        }
                    }
                }
            }
        }
        group "EBGPv4" {
            router "Base" {
                bgp {
                    ebgp-default-reject-policy {
                        import true
                        export true
                    }
                    group "<.*>" {
                        next-hop-self true
                        family {
                            ipv4 true
                        }
                        remove-private {
                            limited true
                        }
                        import {
                            policy ["BGP-BLOCK-ALL"]
                        }
                        export {
                            policy ["BGP-BLOCK-ALL"]
                        }
                        prefix-limit ipv4 {
                            maximum 10
                            log-only false
                            idle-timeout 90
                        }
                    }
                }
            }
        }
        group "EBGPv6" {
            router "Base" {
                bgp {
                    ebgp-default-reject-policy {
                        import true
                        export true
                    }
                    group "<.*>" {
                        next-hop-self true
                        family {
                            ipv6 true
                        }
                        remove-private {
                            limited true
                        }
                        import {
                            policy ["BGP-BLOCK-ALL"]
                        }
                        export {
                            policy ["BGP-BLOCK-ALL"]
                        }
                        prefix-limit ipv6 {
                            maximum 10
                            log-only false
                            idle-timeout 90
                        }
                    }
                }
            }
        }
    }

    {# Common Policy Options and statements used in Peering Manager #}
    policy-options {
        global-variables {
            name "@LOCALPREF@" {
                number 100
            }
        }
        community "GRACEFUL-SHUTDOWN" {
            member "65535:0" { }
        }
        as-path "LARGE-TRANSIT-ASNS" {
            expression ".* (174|209|286|701|702|1239|1299|2828|2914|3257|3320|3356|3491|3549|3561|3908|3910|4134|5511|6453|6461|6762|7018|8928|12956) .*"
        }

        policy-statement "BGP-ACCEPT-IN" {
            entry 10 {
                action {
                    action-type accept
                }
            }
        }
        policy-statement "BGP-ACCEPT-OUT" {
            entry 10 {
                action {
                    action-type accept
                }
                
            }
        }
        policy-statement "BGP-BLOCK-ALL" {
            entry 10 {
                action {
                    action-type reject
                }
            }
        }
        policy-statement "BGP-REJECT-IN" {
            entry 10 {
                action {
                    action-type reject
                }
            }
        }
        policy-statement "BGP-REJECT-OUT" {
            entry 10 {
                action {
                    action-type reject
                }
            }
        }
        policy-statement "BGP_FILTER_GSHUT_IN" {
            entry 60 {
                from {
                    community {
                        name "GRACEFUL-SHUTDOWN"
                    }
                }
                action {
                    action-type accept
                    local-preference 0
                }
            }
        }
        policy-statement "BGP_FILTER_GSHUT_OUT" {
            entry 10 {
                action {
                    action-type accept
                    local-preference 0
                }
            }
        }
        policy-statement "GRACEFUL-SHUTDOWN" {
            entry 10 {
                from {
                    community {
                        name "GRACEFUL-SHUTDOWN"
                    }
                }
                action {
                    action-type accept
                    local-preference 0
                }
            }
        }
        policy-statement "PEER-IN-GSHUT" {
            entry 10 {
                action {
                    action-type next-policy
                    local-preference 0
                }
            }
        }
        policy-statement "PEER-OUT-GSHUT" {
            entry 10 {
                action {
                    action-type next-policy
                    community {
                        add ["GRACEFUL-SHUTDOWN"]
                    }
                }
            }
        }
        policy-statement "PMGR-PEER-IN-V4" {
            {# Add your own AS filtering policy here #}
            entry 100 {
                action {
                    action-type next-policy
                    local-preference "@LOCALPREF@"
                    origin igp
                }
            }
            default-action {
                action-type next-policy
            }
        }
        policy-statement "PMGR-PEER-IN-V6" {
            {# Add your own AS filtering policy here #}
            entry 100 {
                action {
                    action-type next-policy
                    local-preference "@LOCALPREF@"
                    origin igp
                }
            }
            default-action {
                action-type next-policy
            }
        }
        policy-statement "PMGR-PEER-OUT-V4" {
            {# Add your own AS filtering policy here #}
            entry 999 {
                from {
                    policy "ALLOWED-BGP-OUT-V4"
                }
                action {
                    action-type next-policy
                    next-hop self
                }
            }
            default-action {
                action-type reject
            }
        }
        policy-statement "PMGR-PEER-OUT-V6" {
            {# Add your own AS filtering policy here #}
            entry 999 {
                from {
                    policy "ALLOWED-BGP-OUT-V6"
                }
                action {
                    action-type next-policy
                    next-hop self
                }
            }
            default-action {
                action-type reject
            }
        }
    }
}
```


## Nokia SROS Sub - BGP Groups


This part creates the BGP groups that we use in our individual peering sessions. 
The first loop is used to create a BGP group for every Internet Exchange (one for V4 and one for V6)
The second loop is for the groups in Peering Manager. In our case we have Two groups, Transit and Private groups. 


```
{#- By default every IX will be a BGP group with a Apply Group from generic config and default common policy settings  #}
        {%- for ixp in internet_exchange_points %}
          {%- for family in (6, 4) %}
          {%- set gshut = ixp.status == 'pre-maintenance' %}
          {%- set reject = ixp.status == 'maintenance' %}
          delete group {{p}}IXP-{{ ixp.name }}-V{{ family }} 
          group {{p}}IXP-{{ ixp.name }}-V{{ family }} {
            apply-groups ["EBGPv{{ family }}" "EBGP"]
            {%- if ixp.status == 'disabled' %}
            admin-state disable 
            {%- else %}
            admin-state enable 
            {%- endif %}

            {%- for tag in ixp.tags.all() if tag.slug == "origin-validation" %}
            origin-validation {
              ipv{{ family }} true
            }
            {%- endfor %}
             
            {#- BGP Timers if set #}
            {%- if ixp.config_context %}
            {%- if ixp.config_context.timers.hold %}
            hold-time { 
                seconds {{ ixp.config_context.timers.hold }} 
            }
            {%- endif %}
            {%- endif %}
  
            family {
              {% if family == 6 %}ipv6 true{% else %}ipv4 true{%- endif %}
            }
            {%- if ixp | iter_import_policies(family=family) %}
            import {
              policy ["{{p}}{{ ixp | iter_import_policies(family=family)| reverse | join('" "'+p) }}" {%- if gshut %} "PEER-IN-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-IN" {% else  %} "BGP-ACCEPT-IN" {%- endif %}]
            }
            {%- endif %}
            {%- if ixp | iter_export_policies(family=family) %}
            export {
              policy ["{{p}}{{ ixp | iter_export_policies(family=family)| reverse | join('" "'+p) }}" {%- if gshut %} "PEER-OUT-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-OUT" {% else  %} "BGP-ACCEPT-OUT" {%- endif %}]
            }
            {%- endif %}
          }
          {%- endfor %}
        {%- endfor %}

          # PEERING MANAGER BGP GROUPS 
        {#- By default every BGP Group in PM will be a BGP group with default Apply Group from generic config + policy settings  #}
        {%- for group in bgp_groups %}
          {%- for family in (6, 4) %}
          {%- set gshut = group.status == 'pre-maintenance' %}
          {%- set reject = group.status == 'maintenance' %}
          delete group {{p}}{{ group.name }}-V{{ family }} 
          group {{p}}{{ group.name }}-V{{ family }} {
            apply-groups ["EBGPv{{ family }}" "EBGP"]
            {%- if group.status == 'disabled' %}
            admin-state disable 
            {%- else  %}
            admin-state enable 
            {%- endif %}
            {%- for tag in group.tags.all() if tag.slug == "origin-validation" %}
            origin-validation {
              ipv{{ family }} true
            }
            {%- endfor %}
            
            {#- BGP Timers if set #}
            {%- if group.config_context %}
            {%- if group.config_context.timers.hold %}
            hold-time { 
                seconds {{ group.config_context.timers.hold }} 
            }
            {%- endif %}
            {%- endif %}

            family {
              {% if family == 6 %}ipv6 true{% else %}ipv4 true{%- endif %}
            }
            {%- if group | iter_import_policies(family=family) %}
            import {
              policy ["{{p}}{{ group| iter_import_policies(family=family)| reverse | join('" "'+p) }}" {%- if gshut %} "PEER-IN-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-IN" {% else  %} "BGP-ACCEPT-IN" {%- endif %}]
            }
            {%- endif %}
            {%- if group | iter_export_policies(family=family) %}
            export {
              policy ["{{p}}{{ group| iter_export_policies(family=family)| reverse | join('" "'+p) }}" {%- if gshut %} "PEER-OUT-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-OUT" {% else  %} "BGP-ACCEPT-OUT" {%- endif %}]
            }
            {%- endif %}
          }
          {%- endfor %}
        {%- endfor %}
```

## Nokia SROS Sub - BGP Neighbors

This config part creates the individual BGP Neighbors. We have two seperate loops for the IX neighbours and the Transit/Private Peer neighbors.

```
{%- for ixp in internet_exchange_points %}
      {%- for family in (6, 4) %}
          # PEERING MANAGER BGP NEIGHBOURS FROM IX {{ixp.name}} IPv{{family}}
        {%- for session in router | ixp_sessions(family=family, ixp=ixp) %}
        {%- set gshut = ixp.status == 'pre-maintenance' or session.status == 'pre-maintenance' %}
        {%- set reject = ixp.status == 'maintenance' or session.status == 'maintenance' %}
        {%- set disabled = session.status == 'disabled' %}
          delete neighbor {{ session | ip }}
          {%- if session.enabled or disabled or 'maintenance' in session.status %}
          neighbor {{ session | ip }} {
            description "{{ session.autonomous_system.name }}"
            {%- if disabled %}
            admin-state disable
            {%- endif %}
            {%- if session.passive %}
            passive true
            {%- endif %}
            {%- if session.multihop_ttl > 1 %}
            multihop {{session.multihop_ttl}}
            {%- endif %}
            group {{p}}IXP-{{ ixp.name}}-V{{ family }}
            peer-as {{ session.autonomous_system.asn }}
            {%- for tag in session.tags.all() if tag.slug == "origin-validation" %}
            origin-validation {
              ipv{{ family }} true
            }
            {%- endfor %}
            {%- if family == 6 and session.autonomous_system.ipv6_max_prefixes > 0 %}
            prefix-limit ipv6 {
              maximum {{ session.autonomous_system.ipv6_max_prefixes }}
              threshold 90
            }
            {%- endif %}
            {%- if family == 4 and session.autonomous_system.ipv4_max_prefixes > 0 %}
            prefix-limit ipv4 {
              maximum {{ session.autonomous_system.ipv4_max_prefixes }}
              threshold 90
            }
            {%- endif %}

            {#- MD5 Session password if set #}
            {%- if session.encrypted_password %}
            authentication-key "{{ session.encrypted_password }}"
            {%- elif session.password %}
            authentication-key "{{ session.password }}"
            {%- endif %}
 
            {#- BGP Timers if set #}
            {%- if session.config_context %}
            {%- if session.config_context.timers.hold %}
            hold-time { 
                seconds {{ session.config_context.timers.hold }} 
            }
            {%- endif %}
            {%- endif %}

            {#- If Prefix filter is set, we use PREFIX Filter policy + IXP policy, to overwrite the group policy #}
            {#- If Communities are set per Session or per as we will add the Policy for that. Group communities are included group policy#}
            {%- for tag in session.autonomous_system.tags.all() if tag.slug == "filter-prefixes-v" ~ family %}
            import {
              policy ["{{p}}{{ session | merge_import_policies('reverse') | iterate('name')| join('" "'+p) }}" {%- if session | communities | length or session.autonomous_system | communities | length %} "{{p}}COMM-{{ixp.name}}-AS{{session.autonomous_system.asn}}-V{{ family }}-IN" {%- endif %} "{{p}}FROM-AS{{session.autonomous_system.asn}}-V{{ family }}"  {%- if gshut %} "PEER-IN-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-IN" {% else  %} "BGP-ACCEPT-IN" {%- endif %} ]
            }
            {%- else %}
            {%- if session | merge_import_policies| length %}
            import {
              policy ["{{p}}{{ session | merge_import_policies('reverse') | iterate('name') | join('" "'+p) }}" {%-if session | communities | length or session.autonomous_system | communities | length %} "{{p}}COMM-{{ixp.name}}-AS{{session.autonomous_system.asn}}-V{{ family }}-IN" {%- endif %} {%- if gshut %} "PEER-IN-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-IN" {% else  %} "BGP-ACCEPT-IN" {%- endif %} ]
            }
            {%- endif %}
            {%- endfor %}
            {%- if session | merge_export_policies | length %}
            export {
              policy ["{{p}}{{ session | merge_export_policies('reverse') | iterate('name') | join('" "'+p) }}" {%- if gshut %} "PEER-OUT-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-OUT" {% else  %} "BGP-ACCEPT-OUT" {%- endif %}]
            }
            {%- endif %}
          }
          {%- endif %}
        {%- endfor %}
      {%- endfor %}
    {%- endfor %}

    {#- BGP DIRECT NEIGHBOURS #}
    {%- for group in bgp_groups %}
      {%- for family in (6, 4) %}
          # PEERING MANAGER DIRECT BGP NEIGHBOURS GROUP {{group.name}} IPv{{family}}
        {%- for session in router | direct_sessions(family=family, group=group)  %}
          delete neighbor {{ session | ip }}
          {%- set gshut = group.status == 'pre-maintenance' or session.status == 'pre-maintenance' %}
          {%- set reject = group.status == 'maintenance' or session.status == 'maintenance' %}
          {%- set disabled = session.status == 'disabled' %}
          {%- if session.enabled or disabled or 'maintenance' in session.status %}
          neighbor {{ session | ip }} {
            description "{{ session.autonomous_system.name }}"
            {%- if disabled %}
            admin-state disable
            {%- endif %}
            {%- if session.passive %}
            passive true
            {%- endif %}
            {%- if session.multihop_ttl > 1 %}
            multihop {{session.multihop_ttl}}
            {%- endif %}
            group {{p}}{{ group.name}}-V{{ family }}
            peer-as {{ session.autonomous_system.asn }}
            {%- for tag in session.tags.all() if tag.slug == "origin-validation" %}
            origin-validation {
              ipv{{ family }} true
            }
            {%- endfor %}
            {%- if family == 6 and session.autonomous_system.ipv6_max_prefixes > 0 %}
            prefix-limit ipv6 {
              maximum {{ session.autonomous_system.ipv6_max_prefixes }}
              threshold 90
            }
            {%- endif %}
            {%- if family == 4 and session.autonomous_system.ipv6_max_prefixes > 0 %}
            prefix-limit ipv4 {
              maximum {{ session.autonomous_system.ipv4_max_prefixes }}
              threshold 90
            }
            {%- endif %}

            {#- MD5 Session password if set #}
            {%- if session.encrypted_password  %}
            authentication-key "{{ session.encrypted_password }}"
            {%- elif session.password %}
            authentication-key "{{ session.password }}"
            {%- endif %}
          
            {#- BGP Timers if set #}
            {%- if session.config_context %}
            {%- if session.config_context.timers.hold %}
            hold-time { 
                seconds {{ session.config_context.timers.hold }} 
            }
            {%- endif %}
            {%- endif %}

        {#- If Prefix filter is set, we use PREFIX Filter policy + IXP policy, to overwrite the group policy #}
            {#- If Communities are set per Session or per as we will add the Policy for that. Group communities are included group policy#}
            {%- for tag in session.autonomous_system.tags.all() if tag.slug == "filter-prefixes-v" ~ family %}
            import {
              policy ["{{p}}{{ session | merge_import_policies('reverse') | iterate('name')| join('" "'+p) }}" {%- if session | communities | length or session.autonomous_system | communities | length %} "{{p}}COMM-{{group.name}}-AS{{session.autonomous_system.asn}}-V{{ family }}-IN"{%- endif %} "{{p}}FROM-AS{{session.autonomous_system.asn}}-V{{ family }}" {%- if gshut %} "PEER-IN-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-IN" {% else  %} "BGP-ACCEPT-IN" {%- endif %} ]
            } 
            {% else %}
            {%- if session | merge_import_policies| length %}
            import {
              policy ["{{p}}{{ session | merge_import_policies('reverse') | iterate('name') | join('" "'+p) }}" {%- if session | communities | length or session.autonomous_system | communities | length %} "{{p}}COMM-{{group.name}}-AS{{session.autonomous_system.asn}}-V{{ family }}-IN"{%- endif %} {%- if gshut %} "PEER-IN-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-IN" {% else  %} "BGP-ACCEPT-IN" {%- endif %} ]
            }
            {%- endif %}
            {%- endfor %}
            {%- if session | merge_export_policies | length %}
            export {
              policy ["{{p}}{{ session | merge_export_policies('reverse') | iterate('name') | join('" "'+p) }}" {%- if gshut %} "PEER-OUT-GSHUT" {%- endif %}{%- if reject %} "BGP-REJECT-OUT" {% else  %} "BGP-ACCEPT-OUT" {%- endif %}]
            }
            {%- endif %}
          }
          {%- endif %}
        {%- endfor %}
      {%- endfor %}
    {%- endfor %}
```

## Nokia SROS Sub - Route Policy

The part does the creation of the Route Policies. If a route-policy has the tag DONT-EXPORT, we will not export the policy to the router


```
{%- for policy in routing_policies %}
        {%- set dont_export = False %}
        {%- if policy | has_tag('dont-export') %} 
           {%- set dont_export = True %}
        {%- endif %}        
        {#- If router-policy tag is set, look at Router context vars for community based settings #}
        {%- if policy | has_tag('router-policy') %}
          {%- if router.config_context is iterable and not dont_export %}
            {%- set pol_var=router.config_context['policy-variables'] %} 
          {%- endif %}
        {%- else %}
         {%- if router.config_context is iterable and not dont_export %}
           {%- set pol_var=policy.config_context['policy-variables'] %}
         {%- endif %}
        {%- endif %}
        
        {%- if pol_var is defined and pol_var | length > 0 %}
        delete policy-statement {{p}}{{policy.name}}
        policy-statement {{p}}{{policy.name}} {
        {%- if policy.type == "import-policy" %}
          {%- if pol_var['as-path-filter'] is defined %} 
          entry 10 {
            from {
                as-path {
                    name "{{pol_var['as-path-filter']}}"
                }
            }
            action {
                action-type reject
            }
          }
          {%- endif %}
          default-action { 
            action-type next-policy
            {%- if pol_var['local-preference'] is defined %}
            local-preference {{pol_var['local-preference']}}
            {%- endif %} 
            {%- if pol_var['med'] is defined %}
            metric {
                set {{pol_var['med']}}
            }
            {%- endif %} 
            {%- if policy | merge_communities | length %}
            community {
              add ["{{p}}{{ policy | merge_communities | iterate('name') | join('" "'+p)  }}"]
            }
            {%-endif%}
          }
        {%- endif %}
        {%- if policy.type == "export-policy" %}
          {%- if pol_var['comm-deny-to'] is defined %}
          entry 10 {
            from {
                community {
                    name "{{p}}{{pol_var['comm-deny-to']}}"
                }
            }
            action {
                action-type reject
            }
          }
          {%- endif %}
          {%- if pol_var['comm-depref-to'] is defined %}
          entry 20 {
            from {
                community {
                    name "{{p}}{{pol_var['comm-depref-to']}}"
                }
            }
            action {
                action-type next-entry
                as-path-prepend {
                    as-path {{ my_asn }}
                    repeat 1
                }
            }
          }
          {%- endif %}
          default-action { 
            action-type next-policy
            {%- if pol_var['asprepend'] is defined and pol_var['asprepend'] | int > 0 %}
            as-path-prepend {
                as-path {{ my_asn }}
                repeat {{pol_var['asprepend']}}
            }
            {%- endif %}
            {%- if pol_var['med'] is defined %}
            metric {
                set {{pol_var['med']}}
            }
            {%- endif %} 
            {%- if policy | merge_communities | length %}
            community {
              add ["{{p}}{{ policy | merge_communities | iterate('name') | join('" "'+p)  }}"]
            }
            {%-endif%}
          }
        {%- endif %}
        }
        {%- endif %}     
        {%-endfor%}
```

## Nokia SROS Sub - Route Policy Communities

This part is the creation of communities. For every community we want to set on a peer, we create a policy-statement. 

```
{%- for c in communities %}
        community "{{p}}{{ c.name }}" {
          member "{{c.value }}"  { }
        }
        {%-endfor%}

        {#- COMMUNITES POLICIY STATEMENT PARTS #}
        {%- for ixp in internet_exchange_points %}
        {%- for family in (6, 4) %}
        {%- for session in router | ixp_sessions(family=family, ixp=ixp) %}
        {%- if session | communities | length or session.autonomous_system | communities | length %}
        # COMMUNITIES FOR IX SESSIONS {{ixp.name}} IPv{{family}}
        policy-statement "{{p}}COMM-{{ixp.name}}-AS{{session.autonomous_system.asn}}-V{{ family }}-IN" {
          entry 10 {
            action {
             action-type next-entry
             community {
                 add [
              {%- if session | communities | length %}"{{p}}{{ session | communities | join('" "'+p) }}"{%- endif %}
                  {%- if session.autonomous_system | communities | length %} "{{p}}{{ session.autonomous_system | communities  | join('" "'+p) }}"{%- endif %} ]
              }
            }
          }
          default-action {
            action-type next-policy
          }
         }
        {%- endif %}
        {%- endfor %}
        {%- endfor %}
        {%- endfor %}

       
        {%- for group in bgp_groups %}
        {%- for family in (6, 4) %}
        {%- for session in router | direct_sessions(family=family, group=group)  %}
        {%- if session | communities | length or session.autonomous_system | communities | length %}
        # COMMUNITIES FOR DIRECT SESSIONS IPv{{family}}
        policy-statement "{{p}}COMM-{{group.name}}-AS{{session.autonomous_system.asn}}-V{{ family }}-IN" {
          entry 10 {
            action {
              action-type next-entry
              community {
                 add [
                  {%- if session | communities | length %}"{{p}}{{ session | communities | join('" "'+p) }}"{%- endif %}
                  {%- if session.autonomous_system | communities | length %} "{{p}}{{ session.autonomous_system | communities  | join('" "'+p) }}"{%- endif %} ]
              }
            }
          }
          default-action {
            action-type next-policy
          }
         }
        {%- endif %}
        {%- endfor %}
        {%- endfor %}
        {%- endfor %}

```

## Nokia SROS Sub - Route Policy Prefix Lists
```
{%- for as in autonomous_systems %}
        {%- for tag in as.tags.all() if tag.slug == "filter-prefixes-v4" %}

        # IPv4 Prefix-lists for AS{{as.asn}} - {{as.name}}
        {%- if delete_config %}
        delete policy-statement "{{p}}FROM-AS{{as.asn}}-V4"
        {%- endif %}
        policy-statement "{{p}}FROM-AS{{as.asn}}-V4" {
          entry 10 {
            from {
              prefix-list  ["{{p}}FROM-AS{{as.asn}}-V4"]
            }
            action {
              action-type next-policy
            }
          }
          default-action {
            action-type reject
          }
        }

        {%- if delete_config %}
        delete prefix-list "{{p}}FROM-AS{{as.asn}}-V4"
        {%- endif %}
        prefix-list "{{p}}FROM-AS{{as.asn}}-V4" {
        {%- if as.prefixes.ipv4 %}
        {%- for thisprefix in as.prefixes.ipv4 %}
            prefix {{thisprefix.prefix}} {%- if not thisprefix.exact %}  type range {
               start-length {{ thisprefix.prefix.split('/') | last }}
               end-length {{thisprefix['less-equal']}} 
            {%-else%} type exact { {%-endif%} 
            }
        {%- endfor %}
        }
        {%- else %}
           prefix  0.0.0.0/0 type longer {
           }
        }
        {%- endif %}
        {%- endfor %}
        {%- for tag in as.tags.all() if tag.slug == "filter-prefixes-v6" %}

        # IPv6 Prefix-lists for AS{{as.asn}} - {{as.name}}
        {%- if delete_config %}
        delete policy-statement "{{p}}FROM-AS{{as.asn}}-V6"
        {%- endif %}
        policy-statement "{{p}}FROM-AS{{as.asn}}-V6" {
          entry 10 {
            from {
              prefix-list  ["{{p}}FROM-AS{{as.asn}}-V6"]
            }
            action {
              action-type next-policy
            }
          }
          default-action {
            action-type reject
          }
        }

        {%- if delete_config %}
        delete prefix-list "{{p}}FROM-AS{{as.asn}}-V6"
        {%- endif %}
        prefix-list "{{p}}FROM-AS{{as.asn}}-V6" {
        {%- if as.prefixes.ipv6 %}
        {%- for thisprefix in as.prefixes.ipv6 %}
            prefix {{thisprefix.prefix}} {%- if not thisprefix.exact %}  type range {
               start-length {{ thisprefix.prefix.split('/') | last }}
               end-length {{thisprefix['less-equal']}} 
            {%-else%} type exact { {%-endif%} 
            }
        {%- endfor %}
        }
        {%- else %}
           prefix ::/0 type longer {
           }
        }
        {%- endif %}
       {%- endfor %}
       {%- endfor %}

```
