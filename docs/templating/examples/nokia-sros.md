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
      ############### DEFAULT FILTERS ###############
      {% include_configuration "Nokia SROS Sub - Filters" %}
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
     
      ############### IPV4/IPV6 FILTERING ###############
      filter {
        {# FILTER IPv4/IPV6 PART #}
        {%- include_configuration "Nokia SROS Sub - Interface Filters" %}
      }
    }
```

## Nokia SROS Default config
```
### Save this Configuration as 'Nokia SROS Default config' ###
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
