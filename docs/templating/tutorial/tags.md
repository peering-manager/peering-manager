# Use of _Tags_
Peering Manager offers _tags_ you can attach to nearly all elements. They are a great tool to put optional configurations into your template - so no need to request a new checkbox or button for every BGP option you do not want in every session.

Coding a template with tags will even get easier once the new filters for tags have been rolled out. This page shows what currently works in version 1.4.4 and will be changed once there is a new version.

## Example: Using a tag for not enforcing the first AS in an AS path
A common BGP security feature is to check if the first AS in the AS path you receive is the same as the AS of your peer. However, this must be switched off for IXPs route servers (as they do commonly not insert their AS into the path). Coding this for route server can be done as follows:

=== "Cisco IOS XR"
    ```
    router bgp {{ local_as.asn }}
    {%- for ixp in internet_exchange_points %}
      {%- for session in ixp |  sessions %}
        {%- if session.enabled %}
        neighbor {{ session.ip_address }}
        remote-as {{ session.autonomous_system.asn }}
        description {{ session.autonomous_system.name | safe_string }}
        {%-if session.is_route_server %}
        no enforce-first-as
        {%-else%}
        enforce-first-as
        {%-endif%}
        ...
    ```

For any reason you might want to decide yourself on switching this (or any other BGP option) on or off. So here _tags_ come handy. Simply _tag_ the BGP session (mind: the session in this case, not the neighbor AS) where anything other than the default should be applied (it is always a good idea to define a default behaviour and only to tag objects which are different to this default) and use the template to check if the tag is there

In this example I show this for _direct sessions_:

=== "Cisco IOS XR"
    ```
    router bgp {{ local_as.asn }}
    {%- for as in autonomous_systems %}
      {%- for session in as | direct_sessions %}
        {%- if session.enabled %}
        neighbor {{ session.ip_address }}
        remote-as {{ session.autonomous_system.asn }}
        description {{ session.autonomous_system.name | safe_string }}
        {% for tag in session.tags.all() %}
  	     {%- if tag.slug == "no-enforce-first-as" %}no {%-endif%}
        {%-endfor%} enforce-first-as
    ```
    !!!attention
        Be aware of the difference between "{%" and "{%-"
