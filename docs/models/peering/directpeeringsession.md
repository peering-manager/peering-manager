# Direct Peering Session

A direct peering session is a BGP session which is established, most of the
time, over a dedicated link. They can be tied to BGP groups in order to regroup
them logically. Generally, such sessions are made at network exit points with
neighboring hosts outside the AS. They are configured on routers which may or
may not be dedicated to routing Internet traffic.

## In Peering Manager

Inside Peering Manager, you create direct peering sessions to model BGP
sessions established with remote peers and that are not using Internet
exchange LANs. For each direct peering session that you create, the following
properties can be configured (n.b. some are optional):

  * `Local ASN`: an autonomous system to be used by a local router.
  * `Local IP Address`: a local IPv6 or IPv4 address to be bounded on a local
    router.
  * `Autonomous System`: an autonomous system managed by a remote peer.
  * `BGP Group`: a group to which the BGP session belongs to.
  * `Relationship`: a relationship with the remote peer such as customer,
    transit provider or private peer.
  * `IP Address`: an IPv6 or IPv4 address of the remote peer.
  * `Password`: a password to secure a BGP session ; it can be a clear text
    password or an encrypted one. In the latter case, make sure that the router
    will not try to encrypt the password again.
  * `Multihop TTL`: a value to set the time to leave interval for IP packets
    used for the BGP control traffic. It defaults to 1 for external BGP
    sessions but can be set to a higher value to establish sessions that have
    to cross a network composed of more than one router in the transit path of
    the packets.
  * `Enabled`: a value that tells if the session must be configured and
    enabled.
  * `Router`: a router on which the BGP session is supposed to be configured.
  * `Import Routing Policies`: a list of routing policies to apply when
     receiving prefixes though the BGP session.
  * `Export Routing Policies`: a list of routing policies to apply when
     advertising prefixes though the BGP session.
  * `Comments`: text to explain the purposes of the BGP sessions. Can use
    Markdown formatting.
  * `Tags`: a list of tags to help identifying and searching for a BGP session.
