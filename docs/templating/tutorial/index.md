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

We also put the platform of the template into a variable so we can refer to it in the template:

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
* When receiving prefixes, _BGP Communities_ are **set** that control where these prefixes are announced
* When announcing prefixes, existing BGP communities are **checked**, and either announced or not

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

Now with the communities defined, we need to put code into our template to generate the configuration statements.

=== "Cisco IOS"
    ```
    !
    ! Communitiy Lists
    !
    {#- Generate named lists for all communities #}
    {%- for community in communities %}
    ip community-list standard {{p}}{{community.slug}}-{{community.type}} permit {{community.value}}
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

## Routing Policies
