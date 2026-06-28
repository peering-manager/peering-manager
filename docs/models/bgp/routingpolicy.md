# Routing Policy

Routing policies are a set of instructions to apply when advertising to or
receiving prefixes from another autonomous system. They are meant to filter
routes to import or export. Routing policies play an important role in securing
BGP by rejecting invalid routes. Policies can be chained to achieve complex and
effective filtering, while keeping policies as simple as possible.

## In Peering Manager

Inside Peering Manager, you create routing policies by giving each of them a
name. Policies must already exist on the router as their logic cannot be
defined using Peering Manager. For each routing policy that you create, the
following properties can be configured (n.b. some are optional):

* `Name`: human-readable name attached to a routing policy.
* `Slug`: unique configuration and URL friendly name; usually it is
   automatically generated from the routing policy's name.
* `Type`: when to apply the community on ingress or on egress.
* `Weight`: a value that defines the order the policies are chained ; the
  policy with the higher value will be evaluated first.
* `Address Family`: the IP address family the policy can be used for. It can
  be IPv6, IPv4 or both.
* `Configuration Context`: a snippet of JSON that contains additional
  context for e.g. tooling that accesses Peering Manager programmatically.
* `Comments`: text to explain what the routing policy is for. Can use
  Markdown formatting.
* `Tags`: a list of tags to help identifying and searching for a routing
  policy.
