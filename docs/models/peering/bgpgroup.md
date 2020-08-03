# BGP Group

A group of BGP sessions that share, more or less, the same purpose. It is a
common practice to group BGP sessions together. For instance, one may want to
make a group composed of transit provider BGP sessions only. A group can be
defined once but it is not tight to a router. This means that one group can be
configured on several routers depending on which router the BGP sessions are
attached.

## In Peering Manager

Inside Peering Manager, you create a BGP group to aggregate multiple direct BGP
sessions that you want to manage in the same way. A common use case would be to
create one BGP group for transit providers, one for customers and one for
private peering sessions. You can create as many groups as you want depending
on how you want to manage BGP sessions in your network. For each group that you
create, the following properties can be configured (n.b. some are optional):

  * `Name`: a human-readable name attached to a group.
  * `Slug`: a unique configuration and URL friendly name; most of the time it
    is automatically generated from the group's name.
  * `Comments`: text to explain what the group is for. Can use Markdown
    formatting.
  * `Check BGP Session States`: a value used to know if routers attached to BGP
    sessions within the group have to check for the state of these sessions.
  * `Import Routing Policies`: a list of routing policies to apply when
     receiving prefixes though BGP sessions in the group.
  * `Export Routing Policies`: a list of routing policies to apply when
     advertising prefixes though BGP sessions in the group.
  * `Tags`: a list of tags to help identifying and searching for a group.

Please note that an Internet Exchange is a kind of BGP group with more specific
properties aimed to match the purpose of an Internet Exchange network. However
while a group can be configured on more than one router, an IX can only be
attached to a single router. This means that if you are connected more than
once to an IX, you'll have to create one IX object per connection.
