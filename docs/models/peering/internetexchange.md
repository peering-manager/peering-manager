# Internet Exchange

An Internet exchange point, also known as IX or IXP, is an infrastructure
through which autonomous systems exchange traffic. An IX can be a single local
LAN or it can be spread across multiple locations.

## In Peering Manager

Inside Peering Manager, you create an Internet exchange to then create one or
more peering BGP sessions. Only Internet Exchange Peering Sessions can be
related to an Internet exchange. For each Internet exchange you create,
the following properties can be configured (n.b. some are optional):

* `Name`: human-readable name attached to the IX.
* `Slug`: unique configuration and URL friendly name; usually it is
   automatically generated from the IXP's name.
* `Local Autonomous System`: your autonomous system connected to this IX.
* `Comments`: text to explain what the Internet exchange is for. Can use
  Markdown formatting.
* `Check BGP Session States`: whether Peering Manager should poll the state
  of BGP sessions at this IX.
* `Import Routing Policies`: a list of routing policies to apply when
   receiving prefixes though BGP sessions at this IX.
* `Export Routing Policies`: a list of routing policies to apply when
   advertising prefixes though BGP sessions at this IX.
* `PeeringDB ID`: an integer which is the ID of the IX LAN inside PeeringDB.
  This setting is required for Peering Manager to discover potential
  unconfigured BGP sessions.[^1]
* `IPv6 Address`: an IPv6 address used to connect to the Internet exchange
  network. [^2]
* `IPv4 Address`: an IPv4 address used to connect to the Internet exchange
  network. [^2]
* `Router`: a router connected to the Internet exchange. This is used to then
  generate and install configurations.[^2]
* `Tags`: a list of tags to help identifying and searching for a group.

Please note that an Internet exchange is a kind of BGP group with more specific
properties aimed to match the purpose of an Internet exchange network. However
while a group can be configured on more than one router, an IX can only be
attached to a single router. This means that if you are connected more than
once to an IX, you'll have to create one IX object per connection.

[^1]: This is no longer user edible
[^2]: This moved to the [Connection](../../net/connection/) tab
