# AS-based template parts
In this chapter we show how the information Peering Manager contains
about Autonomous Systems can be put into a template.


## Prefix Filtering
Peering Manager has the ability to pull all prefixes an AS should announce from the Internet Registries. Here we show how you can put this information into filter lists for various routers.

As prefix filters can be lengthy you might not want them for every AS, especially you might not want them for IXP route servers. So a _tag_ is  used to tell the template when a prefix list for an AS should be generated.

Also, no prefix list is built if Peering Manager has not yet fetched the prefixes for an AS.

=== "Cisco IOS XR"
    In IOS XR we can put both IPv4 and IPv6 into one _prefix-set_. We also generate a _route-policy_ which checks the prefix set either *drop*s or *pass*es depending on the result. In case we do not want prefix filtering, the policy always passes.

    This policy is then applied by the import policy of the AS (see below).

    Prefix-Set entries are separated by "," except for the last entry. Here the _loop.last_ variable comes handy.

    ```no-highlight
    {%- for as in autonomous_systems %}
      {%- if as | has_tag("prefix-filter") and as.prefixes}
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
      {%-endif%}
    {%-endfor %}
    ```
=== "Cisco IOS"
    Cisco IOS uses prefix-lists, separate for IPv4 and IPv6, for prefix filtering. If the prefix list does not exist or no filtering is wanted, a prefix-list permitting all prefixes is generated.

    We apply the prefix filter directly to the BGP sessins using the _prefix-list <name> in/out_ statement.

    ```no-highlight
    {%- for as in autonomous_systems %}
      {%- if as | has_tag("prefix-filter") and as.prefixes}
    !
    ! Prefix-lists for AS{{as.asn}}
    ! {{as.name}}
    !
    no ip prefix-list from-as{{as.asn}}
        {%- for thisprefix in as.prefixes.ipv4 %}
    ip prefix-list from-as{{as.asn}} permit {{thisprefix.prefix}}
          {%- if not thisprefix.exact %} le {{thisprefix['less-equal']}}{%-endif%}
        {%- endfor %}
    !
    no ipv6 prefix-list from-as{{as.asn}}
        {%- for thisprefix in as.prefixes.ipv6 %}
    ipv6 prefix-list from-as{{as.asn}} permit {{thisprefix.prefix}}
          {%- if not thisprefix.exact %} le {{thisprefix['less-equal']}}{%-endif%}
        {%- endfor %}
    !
      {%-else%}
    {#- Delete old set if still exists #}
    no ip prefix-list from-as{{as.asn}}
    no ipv6 prefix-list from-as{{as.asn}}
    ip prefix-list from-as{{as.asn}} permit 0.0.0.0/0 le 32
    ipv6 prefix-list from-as{{as.asn}} permit ::0/0 le 128
    !
      {%-endif%}
    {%-endfor %}
    ```
=== "Juniper"

=== "Mikrotik"

=== "Nokia"

!!!attention
    Only Cisco IOS XR has been tested.

## Import and Export Policies

=== "Cisco IOS XR"
    ```no-highlight
    {%- for as in autonomous_systems %}
      
