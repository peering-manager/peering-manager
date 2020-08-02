# Internet Exchange

An Internet exchange point, also known as IX or IXP, is an infrastructure
through which autonomous systems exchange traffic. An IX can be a single local
LAN or it can be spread across multiple locations.

## In Peering Manager

Inside Peering Manager, you create an Internet exchange to then create one or
more peering BGP sessions. Only Internet Exchange Peering Sessions can be
related to an Internet exchange. For each Internet exchange that you create,
the following properties are to be provided (some are however optional):

  * `Name`: a human readable name attached to a group.
  * `Slug`: a unique configuration and URL friendly name; most of the time it
    is automatically generated from the group's name.
  * `Comments`: some text that can be formatted in Markdown to explain what the
    Internet Exchange is for or to use for any other purposes.
  * `Check BGP Session States`: a value used to know if routers attached to BGP
    sessions within the group have to check for the state of these sessions.
  * `Import Routing Policies`: a list of routing policies to apply when
     receiving prefixes though BGP sessions in the group.
  * `Export Routing Policies`: a list of routing policies to apply when
     advertising prefixes though BGP sessions in the group.
  * `PeeringDB ID`: an integer which is the ID of the IX LAN inside PeeringDB.
    This setting is required for Peering Manager to discover potential
    unconfigured BGP sessions.
  * `IPv6 Address`: an IPv6 address used to connect to the Internet exchange
    network.
  * `IPv4 Address`: an IPv4 address used to connect to the Internet exchange
    network.
  * `Router`: a router connected to the Internet exchange. This is used to then
    generate and send configurations.
  * `Tags`: a list of tags to help identifying and searching for a group.

Please note that an Internet Exchange is a kind of BGP group with more specific
properties aimed to match the purpose of an Internet Exchange network. However
while a group can be configured on more than one router, an IX can only be
attached to a single router. This means that if you are connected more than
once to an IX, you'll have to create one IX object per connection.
