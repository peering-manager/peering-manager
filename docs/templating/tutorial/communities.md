# BGP Communities
Peering Manager allows communities to be applied to the following parts of the configuration:
    - Autonomous Systems
    - Internet Exchanges
    - BGP Groups

So in these three sections of our template we must check if communities need to be applied. What makes life interesting is, that there are three kind of communities which router platform often handle differently but which are not (yet) distinguished in Peering Manager.

This makes it currently necessary to apply a _tag_ to each community. The following tags are used in this tutorial:
    - normal-community
    - extended-community
    - large-community
Untagged communities are simply not exported.

The following template code only shows how large communities are exported - the syntax for extended and normal communities is similar.

The outer for-loop has to be done for all three locations where communities can be applied, we show it here for Autonomous Systems only.

=== "Cisco IOS XR"
    !!!attention
        At the end a "dummy-community" of _your-as-number:9999:9999_ is added. This is done because IOS XR expects a comma after each community except the last and the _loop.last_ variable does not work here. Once I find a better solution I will update this code.

    ```no-highlight
    {%- for as in autonomous_systems %}
    !
    ! Communities for AS{{as.asn}}
    large-community-set large-communities-as{{ as.asn }}-in
      {%- for community in as.communities.all() %}
        {%-if community.type == "ingress" and community | has_tag("large-community")%}
          {{ community.value }},
        {%- endif %}
      {%- endfor %}
     {{local_as.asn}}:9999:9999
    end-set
    large-community-set large-communities-as{{ as.asn }}-out
      {%- for community in as.communities.all() %}
        {%- if community.type == "egress" and community | has_tag("large-community")%}
          {{ community.value }},
    	  {%- endif %}
      {%- endfor %}
     {{local_as.asn}}:9999:9999
    end-set
    !
    {%-endfor%}
    ```
    Result of this looks may look like:
    ```no-highlight
    large-community-set large-communities-as64500-in
      196610:0:21200,
      196610:1:41000,
      196610:9999:9999
    end-set
    large-community-set large-communities-as64500-out
      196610:9999:9999
    end-set
    ```
=== "Cisco IOS"
    ```no-highlight
    
