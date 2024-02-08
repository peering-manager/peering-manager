# Nokia SROS template 
The NOKIA SROS template has been created and tested on two virtual SROS 7750 routers running in a Containerlab environment. 
This template uses a Main and sub templates. The main template includes sub templates for the different parts of the configuration.

## Nokia SROS Main template
```
### Save this Configuration as 'Nokia SROS Main template' ###

{#- Generic Nokia SROS Template #}
{#- We define the type of template for reference #}
{%- set template_type="nokia-sros"%}
{#- We delete the config blocks and do recreate of it to be sure we delete removed config blocks #}
{%- set delete_config = true %}
{#- To avoid conflict with prefedined elements, we prefix everything we define#}
############### DEFAULT CONIG ###############
{#- Default config contains all static config elements. This will be very specific per AS/Router #}
{% include_configuration "Nokia SROS Default config" %}
{%- set p="PMGR-"%}
    configure {
      router "Base" {
        {#- START OF BGP CONFIG #}
        bgp {
        
        {#- BGP GROUPS #}
          ############### BGP GROUPS ###############
        {%- include_configuration "Nokia SROS Sub - BGP Groups" %}

        {#- BGP IXP NEIGHBOURS #}
          ############### BGP NEIGHBOURS ###############
        {%- include_configuration "Nokia SROS Sub - BGP Neighbors" %}

        }
      }

      {#- ROUTING POLICY PART #}

      ############### ROUTING POLICY ###############
      policy-options {
        {#- ROUTING POLICY GENERIC #}
        ############### ROUTING POLICY GENERIC ###############
        {%- include_configuration "Nokia SROS Sub - Route Policy" %}

        {#- COMMUNITIES #}
        ############### COMMUNITIES ###############
        {%- include_configuration "Nokia SROS Sub - Route Policy Communities" %}

        {#- Prefix Lists#}
        ############### PREFIX LISTS###############
        {%- include_configuration "Nokia SROS Sub - Route Policy Prefix Lists" %}
      }
     
    }
```

## Nokia SROS Default config
```
### Save this Configuration as 'Nokia SROS Default config' ###
#
# This is the static part of the config.
# The group parts we include in other config are the groups IBGP/EBGP/IBGPv4/IBGPv6/EBGPv4/EBGPv6
# The policy-maps we use are for generic filtering are PMGR-PEER-IN-V4 / PMGR-PEER-IN-V6 / PMGR-PEER-OUT-V4 / PMGR-PEER-OUT-V6.
# The policy-maps we use are defaults are BGP-ACCEPT-IN / BGP-ACCEPT-OUT / BGP-REJECT-IN / BGP-ACCEPT-OUT / BGP-BLOCK-ALL
# For Gracefull Shutdown we use the policy-maps PEER-IN-GSHUT / PEER-OUT-GSHUT

configure {
    groups {
        group "IBGP" {
            router "Base" {
                bgp {
                    group "<.*>" {
                        keepalive 30
                        min-route-advertisement 1
                        aigp true
                        multipath-eligible true
                        hold-time {
                            seconds 90
                            minimum-hold-time 90
                        }
                    }
                }
            }
        }
        group "IBGPv4" {
            router "Base" {
                bgp {
                    group "<.*>" {
                        next-hop-self true
                        aigp false
                        family {
                            ipv4 true
                        }
                        prefix-limit ipv4 {
                            maximum 2000
                            log-only false
                            idle-timeout 90
                        }
                        graceful-restart {
                        }
                    }
                }
            }
        }
        group "IBGPv6" {
            router "Base" {
                bgp {
                    group "<.*>" {
                        next-hop-self true
                        aigp false
                        family {
                            ipv6 true
                        }
                        prefix-limit ipv6 {
                            maximum 200
                            log-only false
                            idle-timeout 90
                        }
                        graceful-restart {
                        }
                    }
                }
            }
        }
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
       
    policy-options {
        global-variables {
            name "@ASFILTER@" {
                number 0
            }
            name "@ASPREPEND@" {
                number 0
            }
            name "@LOCALPREF@" {
                number 100
            }
            name "@PFXFILTER_V4@" {
                value "ANY-V4"
            }
            name "@PFXFILTER_V6@" {
                value "ANY-V6"
            }
        }
        prefix-list "ANY-V4" {
            prefix 0.0.0.0/0 type longer {
            }
        }
        prefix-list "ANY-V6" {
            prefix ::/0 type longer {
            }
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
        policy-statement "BGP_FILTER_GSHUT_OUT" {
            entry 10 {
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
            default-action {
                action-type next-policy
            }
        }
        policy-statement "PMGR-PEER-IN-V6" {
            default-action {
                action-type next-policy
            }
        }
        policy-statement "PMGR-PEER-OUT-V4" {
            default-action {
                action-type next-policy
            }
        }
        policy-statement "PMGR-PEER-OUT-V6" {
            default-action {
                action-type next-policy
            }
        }
    }
		

    router "Base" {
        autonomous-system 65543
        bgp {
            preference 200
            router-id 192.168.1.1
            rapid-withdrawal true
            local-as {
                as-number 65543
            }
        }
    }
    
}
```

## Nokia SROS Sub - BGP Groups
```
### Save this Configuration as 'Nokia SROS Sub - BGP Groups' ###

{#- By default every IX will be a BGP group with a Apply Group from generic config and default common policy settings  #}
        {%- for ixp in internet_exchange_points %}
          {%- for family in (6, 4) %}
          {%- set gshut = ixp.status == 'pre-maintenance' %}
          {%- set reject = ixp.status == 'maintenance' %}
          delete group {{p}}IXP-{{ ixp.name }}-V{{ family }} 
          group {{p}}IXP-{{ ixp.name }}-V{{ family }} {
            apply-groups ["EBGPv{{ family }}" "EBGP"]
            {%- if ixp.status == 'maintenance' %}
            admin-state disable 
            {%- elif ixp.status == 'disabled' %}
            admin-state disable 
            {%- else %}
            admin-state enable 
            {%- endif %}

            {%- for tag in ixp.tags.all() if tag.slug == "origin-validation" %}
            origin-validation {
              ipv4 true
              ipv6 true
            }
            {%- endfor %}
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
              ipv4 true
              ipv6 true
            }
            {%- endfor %}
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
```
### Save this Configuration as 'Nokia SROS Sub - BGP Neighbors' ###

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
              ipv4 true
              ipv6 true
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
            {%- if session.encrypted_password %}
            authentication-key "{{ session.encrypted_password }}"
            {%- elif session.password %}
            authentication-key "{{ session.password }}"
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
              ipv4 true
              ipv6 true
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

            {#- MD5 Session password if set #}
            {%- if session.encrypted_password %}
            authentication-key "{{ session.encrypted_password }}"
            {%- elif session.password %}
            authentication-key "{{ session.password }}"
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
```
### Save this Configuration as 'Nokia SROS Sub - Route Policy' ###

{%- for policy in routing_policies %}
        {%- set dont_export = False %}
        {%- if policy | has_tag('dont-export') %} 
           {%- set dont_export = True %}
        {%- endif %}        
        {#- If router-policy tag is set, look at Router context vars for community based settings #}
        {% if policy | has_tag('router-policy') %}
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
                    as-path 65543
                    repeat 1
                }
            }
          }
          {%- endif %}
          default-action { 
            action-type next-policy
            {%- if pol_var['asprepend'] is defined and pol_var['asprepend'] | int > 0 %}
            as-path-prepend {
                as-path 65543
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
```
### Save this Configuration as 'Nokia SROS Sub - Route Policy Communities' ###

{%- for c in communities %}
        community "{{p}}{{ c.name }}" {
          member "{{c.value }}"  { }
        }
        {%-endfor%}
        

        {#- COMMUNITES POLICIY STATEMENT PARTS #}
        {%- for ixp in internet_exchange_points %}
        {%- for family in (6, 4) %}
        # COMMUNITIES FOR IX SESSIONS {{ixp.name}} IPv{{family}}
        {%- for session in router | ixp_sessions(family=family, ixp=ixp) %}
        {%- if session | communities | length or session.autonomous_system | communities | length %}
        policy-statement "{{p}}COMM-{{ixp.name}}-AS{{session.autonomous_system.asn}}-V{{ family }}-IN" {
          entry 10 {
            action {
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
        # COMMUNITIES FOR DIRECT SESSIONS IPv{{family}}
        {%- for session in router | direct_sessions(family=family, group=group)  %}
        {%- if session | communities | length or session.autonomous_system | communities | length %}
        policy-statement "{{p}}COMM-{{group.name}}-AS{{session.autonomous_system.asn}}-V{{ family }}-IN" {
          entry 10 {
            action {
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
### Save this Configuration as 'Nokia SROS Sub - Route Policy Prefix Lists' ###

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
