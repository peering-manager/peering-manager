# Templating Tutorial
This tutorial will try to enable you to write your own templates or modify
one of the examples to your needs.

Templates are highly individual to each network, so there is no
"one size fits all".

The purpose of a template is to translate information stored in Peering Manager
into a syntactically and semantically correct router configuration.

There are several design decisions you must take when writing your own template:

1. What to put into the template and what to keep out of it.
Sounds trivial, but a router configuration can be complex.
Roughly, there are two ways to approach this:
    - Self contained template: There are no references from the template to
    the "outside" of it.
    Means that all policies, route maps, lists, etc. referenced in the template
    are also defined in the template.
    This does not mean that there is no configuration on the router(s)
    themselves - just no reference from inside the template to it.
    - Template with outside references: Things that rarely change like community
    lists, route-maps are kept out of the template and configured on the router.
    The template simply refers to them where needed.
2. Which part(s) of Peering Manager to use: You might not need all features of
Peering Manager in your template.
For example, I did not use BGP Groups.
You might only use it to configure BGP sessions and leave all Communities or
Policies out.
Its all up to you.

This tutorial will give you the building blocks of templates.
The actual design and build you must do yourself according to your needs.

We are building the template step by step from the beginning. The following
syntax is used in this document:

!!! todo
    This marks tasks you need to do using the web interface of Peering Manager

```
This goes into your template.
Don't worry - the complete template we are building will be listed at the end.
```


## Building an example template
Peering Manager should manage your peerings - well, it's in the name. So the
template suggested here takes care of:

* No conflict with existing configurations on your router(s).
* Adding new peerings: When a peering request comes in, you only will have to
select the AS and IXP where to peer. Rest is done automatically, including:
    * Building and attaching prefix filters (if wanted)
    * Setting communities incoming (and outgoing)
    * Building a _route-map_ or _route-policy_ or what ever your platform
    supports for filtering receiving and announcing prefixes.

To achieve the goal lets set a few variables at the beginning of your template -
we are prepending every configuration item in our router by a specific string to
make sure nothing is overwritten what is already there.

```
{#- To avoid conflict with prefedined elements,
we prepend everything we define#}
{%- set p="pm-"%}
```

We also put the platform of the template into a variable so we can refer to it
in the template:

=== "Cisco IOS"
    ```
    {#- We define the type of template for reference #}
    {%- set template_type="cisco-ios"%}
    ```

=== "Cisco IOS XR"
    ```
    {#- We define the type of template for reference #}
    {%- set template_type="cisco-iosxr"%}
    ```


## Configuration design
For all configs the following design decisions are applied:

* We distinguish between three types of eBGP sessions:
    * Customers
    * Peers
    * Transit
* The policy for announcing prefixes is as follows:
    * Customer prefixes are announced to customers, peers, transit (= all)
    * Peer prefixes are announced to customers (only)
    * Transit prefixes are announced to customers (only)
* When receiving prefixes, _BGP Communities_ are **set** that control where
these prefixes are announced
* When announcing prefixes, existing BGP communities are **checked**, and either
announced or not

## BGP Communities

The following communities are used for this example:

| Announce to | Community            |
|-------------|----------------------|
| Nobody      | 65500:40000 or empty |
| Customers   | 65500:41000          |
| Peers       | 65500:42000          |
| Transit     | 65500:44000          |

If want to combine them, simply set two or more communities.

!!! question
    Why these numbers?
    I have been using them for years and simply copied them from my router.
    Cisco allows _regular expression parsing_ of communities and the '4' as the
    first digit in my case means 'control announcement'.

!!! todo
    Define the communities listed above in Peering Manager. Give them meaningful
    names like "Announce to Customers" and set their type to **ingress** (as
    they are _set_ when receiving prefixes).

Now with the communities defined, we need to put code into our template to
generate the configuration statements.

We also build a "delete list" of all communities we are using internally so we
can delete them from received prefixes.

=== "Cisco IOS"
    ```
    !
    ! Communitiy Lists
    !
    {#- Generate named lists for all communities #}
    {%- for community in communities %}
    ip community-list standard {{p}}{{community.slug}}-{{community.type}} permit {{community.value}}
    ip community-list standard {{p}}comm-delete permit {{community.value}}
    {%-endfor%}
    !
    ```

    Output for our example looks like:
    ```
    !
    ! Communitiy Lists
    !
    ip community-list standard pm-announce-to-nobody-ingress permit 65500:40000
    ip community-list standard pm-announce-to-customers-ingress permit 65500:41000
    ip community-list standard pm-announce-to-peers-ingress permit 65500:42000
    ip community-list standard pm-announce-to-upstream-ingress permit 65500:44000
    !
    ip community-list standard pm-comm-delete permit 65500:40000
    ip community-list standard pm-comm-delete permit 65500:41000
    ip community-list standard pm-comm-delete permit 65500:42000
    ip community-list standard pm-comm-delete permit 65500:44000
    ```


=== "Cisco IOS XR"
    ```
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
    !
    ```

!!! remark
    In practise on a modern router we would use _Large Communities_.
    But as some old routers still do not support them, we stick with
    regular communities for this example.

With the communities defined, we now need to apply them to ASes or IXPs. If you
only peer at an IXP (have no transit or cusomer relationships) you can only
apply them to the IXP, no need to also apply them to every AS.

!!! todo
    Have an IXP configured in Peering Manager, and apply the "Announcd to
    Customers" community as _ingress_ BGP community.

## Prefix filtering
Peering Manager uses [bgpq3](http://snar.spb.ru/prog/bgpq3/) to build prefix
filters. You might not want that for every peer, especially if you peer with a
route server who, like the DE-CIX route servers, [already
filter](https://www.de-cix.net/en/locations/frankfurt/route-server-guide).

To enable filtering for a peering AS, we use a _tag_.

!!! todo
    Create a _tag_ in peering manager and give it a name like "Filter Prefixes"

=== "Cisco IOS"
    In IOS we have to handle IPv4 and IPv6 separately. We create two _prefix
    lists_ which we later attach to the peering session(s) for tagged ASes. In
    case we do not want to filter we also create a prefix list allowing
    everything - this makes the templating for the BGP session easier.

    ```
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
      {#- no filtering #}
    ip prefix-list {{p}}from-as{{as.asn}} permit 0.0.0.0/0 le 32
    ipv6 prefix-list {{p}}from-as{{as.asn}} permit ::0/0 le 128
    !
      {%-endfor%}
    {%-endfor%}
    ```

    This is later attached to the BGP session like this:
    ```
    ...
      neighbor {{ session.ip_address }} prefix-list {{p}}from-as{{as.asn}} in
    ...
    ```

=== "Cisco IOS XR"
    IOS XR has _prefix sets_ in which you can mix IPv4 and IPv6 prefixes. This
    makes the template easier. Also, we create a _route-policy_ to check the
    prefixes and if filtering is not wanted we simply do a policy containing
    only a _pass_ statement (allowing all).

    ```
    {%- for as in autonomous_systems %}
      {%- for tag in as.tags.all() if tag.slug == "filter-prefixes" and as.prefixes %}
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
    {%-endfor %}
    ```


## Routing Policies
With Communities an Prefix Lists in place, we can now define some routing
policies and that part of the template which converts them into router
configurations.

Here we really have to be very platform specific. In some platforms like IOS XR
the template looks very short and easy to understand, while for others like old
Cisco IOS we have to make some compromises.

Inside Peering Manager a policy is simply a piece of JSON - but that allows us
to put code for multiple platforms into it.

!!! todo
    Add a _Routing Policy_ in Peering Manager with a name like "peering-out".
    Define it as an _Export_ policy and put the follwing JSON into the _Config
    Context_:
    ```JSON
    {
    "cisco-ios": [
        {
            "match": [
                "community pm-announce-to-peers-ingress"
            ],
            "result": "permit"
        }
    ],
    "cisco-iosxr": [
        "if community matches-any pm-announce-to-peers-ingress then",
        "  pass",
        "else",
        "  drop",
        "endif"
    ]
    }
    ```
Using this format allows to put policies for more than one platform into the config context. Of course, if you only have one router platform you can rewrite this to your needs.

We have to do the same for incoming.

!!! todo
    Add a _Routing Policy_ in Peering Manage and name it like "peering-in".
    Define it as an _Import_ policy and put the following JSON into the _Config
    Context_:
    ```JSON
    {
    "cisco-ios": [
        {
            "set": [
                "local-preference 1000"
            ],
            "result": "permit"
        }
    ],
    "cisco-iosxr": [
        "set local-preference 1000",
        "pass"
    ]
    }
    ```

Now we define templates for the different platforms.

=== "Cisco IOS"
    In IOS we can apply _one_ route-map to each BGP session. So we iterate over
    all enabled IXP sessions and generate route-maps (one for in, one for out).

    Peering Managers filter ```merge_import_policies``` does the work of putting
    all the policies (of IXPs, ASes, and sessions) together, see the
    documentation for how this is done.

    We have to generate one route-map for all policies defined.

    - We put an explicit _deny_ clause at the end, as there is no implicit deny
    when "continue" is used.
    - For incoming, we first delete all our own communities and use a _continue_
    statement to go on
    - Then we add all IXP communities, and also _continue_
    - "result" goes into the header of the route-map clause
    - "set" and "match" statements are simply printed out
    - numbering is done automatically, iteration of the outer loop multiplied by
    1000
    - For the "in" route-map, communities are applied to all "permit" clauses

    ```
    {%- for ixp in internet_exchange_points %}
      {%- for session in ixp |  sessions %}
        {%- if session.enabled %}
    ! Session with AS{{session.autonomous_system.asn}} ID:{{ session.id }} at {{ixp.name}}
    ! First delete all our own communities incoming
    route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in permit 1
      set comm-list {{p}}comm-delete delete
      continue
    !
    ! then set all required communities for this IXP
    route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in permit 2
          {%-for community in ixp.communities.all() %}
            {%-if community.type == "ingress"%}
      set community {{community.value}} additive
            {%-endif%}
          {%-endfor%}
      continue
    ! In: {{session | merge_import_policies |  iterate('slug') | join(',') }}
          {%-for policy in session | merge_import_policies%}
            {%-set outer=loop.index%}
            ! {{policy.slug}}
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
          route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out permit 1
          {%-for community in ixp.communities.all() %}
            {%-if community.type == "egress"%}
                set community {{community.value}} additive
            {%-endif%}
          {%-endfor%}
          continue
          !
          {%-for policy in session | merge_export_policies%}
    ! Out: {{session | merge_export_policies |  iterate('slug') | join(',') }}
            {%-set outer=loop.index%}
            ! {{policy.slug}}
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
    ```



=== "Cisco IOS XR"
