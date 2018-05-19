# User Manual

## Objects in Peering Manager

Peering Manager uses objects to represent autonomous systems, Internet exchange
points, peering sessions, routers and more. These objects are composed of
fields aiming to contain different types of value.

This user manual describes some of the objects that Peering Manager uses and
that users are going to work with.

### Autonomous System

TODO

### Internet Exchange

An **Internet Exchange (IX)** is an object representing a connection of a
network to an IX. It is composed of the following fields:

  * a **name**, it can be a string composed of any characters.
  * a **slug**, it can be any lower case strings that must be unique for each
    Internet Exchange.
  * an **IPv6 address**, it should be the IPv6 address used to connect to the
    Internet Exchange, this field can be left empty.
  * an **IPv4 address**, it should be the IPv4 address used to connect to the
    Internet Exchange, this field can be left empty.
  * a **configuration template**, it is the `Template` object to be used to
    generate a configuration depending of the IX fields and the peering
    sessions associated to it.
  * a **router**, it is the `Router` object to be used to be able to push
    configuration changes on the network device.
  * a **PeeringDB ID**, it is an optional field that can be used to link the IX
    object to a PeeringDB entry to automate some features using PeeringDB data.
    If the IX are imported from PeeringDB this field will be automatically
    filled. If you want to find the PeeringDB ID to enter in this field while
    editing the IX object you can use your IX IPv6 or IPv4 address with these
    given URL and note the `id` field's value (it must be a number).

    ```
    https://peeringdb.com/api/netixlan?ipaddr4=${YOUR_IPV4_ADDRESS}
    https://peeringdb.com/api/netixlan?ipaddr6=${YOUR_IPV6_ADDRESS}
    ```
  * **comments**, it is an optional field that can be used to take some notes
    about the object. It supports the
    [GitHub Markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)
    syntax.

### Community

A **Community** is an object representing a BGP community. It can be a standard
BGP community (RFC1997) or a BGP large community (RFC8092). It is composed of
the following fields:

  * a **name**, it can be a string composed of any characters.
  * a **value**, it is the actual value of the community that will be sent as
    BGP attribute.
  * a **type**, it can be *Egress* or *Ingress* depending of when the community
    has to be applied (upon routes receiving or upon routes advertising).
  * **comments**, it is an optional field that can be used to take some notes
    about the object. It supports the
    [GitHub Markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)
    syntax.

### Router

TODO

### Template

TODO
