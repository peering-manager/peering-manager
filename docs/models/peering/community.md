# Community

BGP communities are attribute tags that can be applied to received or
advertised prefixes. They are defined by three main RFCs:

  * [RFC1997](https://tools.ietf.org/html/rfc1997) — BGP Communities
  * [RFC4360](https://tools.ietf.org/html/rfc4360) — BGP Extended Communities
  * [RFC8092](https://tools.ietf.org/html/rfc8092) — BGP Large Communities

Communities can be used to tell other autonomous systems what to do with the
prefixes having them. For instance it can be used tell an AS to restrict
advertisement of a prefix to only Europe peering customers. While network
service providers tends to publish a list of communities to use for them to
apply special treatments some communities are reserved. Blackholing IPs, for
example, can be achieved with [RFC7999](https://tools.ietf.org/html/rfc7999)
community.

## In Peering Manager

Inside Peering Manager, you create communities to apply them on autonomous
systems, BGP groups, Internet Exchanges or BGP sessions. For each community
that you create, the following properties are to be provided (some are however
optional):

  * `Name`: a human readable name attached to a community.
  * `Slug`: a unique configuration and URL friendly name; most of the time it
    is automatically generated from the community's name.
  * `Value`: actual value of the community depending of the RFC.
  * `Type`: when to apply the community on ingress or on egress.
  * `Comments`: some text that can be formatted in Markdown to use to explain
    what the group is for or to use for any other purposes.
  * `Tags`: a list of tags to help identifying and searching for a community.
