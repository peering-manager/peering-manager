# Templating Tutorial
This tutorial will try to enable you to write your own templates or modify
one of the examples to your needs.

Templates are highly individual to each network, so there is no "one size fits all".

The purpose of a template is to translate information stored in Peering Manager
into a syntactically and semantically correct router configuration.

There are several design decisions you must take when writing your own template:

1. What to put into the template and what to keep out of it. Sounds trivial, but
a router configuration can be complex. Roughly, there are two ways to approach this:
    - Self contained template: There are no references from the template to
    the "outside" of it. Means that all policies, route maps, lists, etc. referenced
    in the template are also defined in the template.
    This does not mean that there is no configuration on the router(s) themselves -
    just no reference from inside the template to it.
    - Template with outside references: Things that rarely change like community
    lists, route-maps are kept out of the template and configured on the router.
    The template simply refers to them where needed.
2. Which part(s) of Peering Manager to use: You might not need all features of
Peering Manager in your template. For example, I did not use BGP Groups. You
might only use it to configure BGP sessions and leave all Communities or Policies out. Its all up to you.

This tutorial will give you the building blocks of templates. The actual design
and build you must do yourself according to your needs.
