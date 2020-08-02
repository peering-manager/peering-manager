# Routing Policy

Routing policies are a set of instructions to apply when advertising or
receiving prefixes from another autonomous system. They are meant to filter
routes to import or export. Routing policies play an important role to secure
BGP by rejecting routes that does not belong in the Internet. Policies can in
most cases be chained to achieve a complex and effective filtering process
while keeping policy as simple as possible.

## In Peering Manager

Inside Peering Manager, you create routing policies by giving each of them a
name. Policies must already exist on the router as their logics cannot be
defined using Peering Manager. For each routing policy that you create, the
following properties are to be provided (some are however optional):

  * `Name`: a human readable name attached to a routing policy.
  * `Slug`: a unique configuration and URL friendly name; most of the time it
    is automatically generated from the routing policy's name.
  * `Type`: when to apply the community on ingress or on egress.
  * `Weight`: a value that defines the order the policies are chained ; the
    policy with the higher value will be evaluated first.
  * `Address Family`: the IP address family the policy can be used for ; it can
    be IPv6, IPv4 or both of them.
  * `Comments`: some text that can be formatted in Markdown to explain what the
    routing policy is for or to use for any other purposes.
  * `Tags`: a list of tags to help identifying and searching for a routing
    policy.
