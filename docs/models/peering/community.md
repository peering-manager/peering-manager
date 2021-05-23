# Community

BGP communities are attribute tags that can be applied to received or
advertised prefixes. They are defined by three main RFCs:

* [RFC1997](https://tools.ietf.org/html/rfc1997) — BGP Communities
* [RFC4360](https://tools.ietf.org/html/rfc4360) — BGP Extended Communities
* [RFC8092](https://tools.ietf.org/html/rfc8092) — BGP Large Communities

Communities can be used to tell other autonomous systems what to do with these
prefixes. For instance they can be used tell an AS to restrict advertisement
of a prefix to only Europe peering customers. Most good network service
providers publish a list of communities they will honor. Note that some
communities are reserved. Blackholing IPs, for example, can be achieved with
[RFC7999](https://tools.ietf.org/html/rfc7999) community.

## In Peering Manager

Inside Peering Manager, you create communities to apply them on autonomous
systems, BGP groups, Internet Exchanges or BGP sessions. For each community
that you create, the following properties can be configured (n.b. some are
optional):

* `Name`: human-readable name attached to a community.
* `Slug`: unique configuration and URL friendly name; usually it is
   automatically generated from the community's name.
* `Value`: actual value of the community.
* `Type`: when to apply the community - on ingress or egress.
* `Comments`: text to explain what the community is for. Can use Markdown
  formatting.
* `Tags`: a list of tags to help identifying and searching for a community.
