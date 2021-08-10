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

## Platform specialities
All platforms are different and some platforms lack certain features. Peering
Manager itself is platform independent. That does not mean that everything you
configure inside Peering Manager can be rolled out to every platform.

This overview here will focus on the limits of the platforms featured in the
examples of this tutorial.

### Cisco IOS XR
The 'modern' Cisco platform. Lots of features and nearly everything can be put
into a template. One issue to be aware of are the handling of _BGP Communities_
- Peering Manager has only one type of community and you can simply enter a
Large, Extended or Normal value. Cisco IOS XR handles these three differently,
so the template must somehow find out the type of a community. At the moment a
_tag_ in Peering Manager is used for that.

For policies, it is possible to _apply_ one policy inside another, so all
configured policies in Peering Manager can go one-to-one into the template and a
"session policy" can then call each of them. To check out if the resulting
policy is ok, you can use ```show rpl route-policy _name_ inline``` command.

### Cisco IOS
The 'old' Cisco platform - quite limited in features. You can attach only _one_
route-map to each BGP session. So if you have multiple policies applied to
various objects, they need to be "flattened" into one route-map. The suggestion
here is to keep things simple and try not to use too many features. Also be
aware of the ordering of statements, if in doubt, check the configuration
produced before you apply it.
