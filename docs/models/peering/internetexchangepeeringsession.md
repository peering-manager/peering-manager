# Internet Exchange Peering Session

An Internet exchange peering session is a BGP session which is established over
an Internet exchange LAN. When peering on an IX, it is a common practice to
create BGP sessions with route servers (if they are any) and other autonomous
systems which you want to reach directly without having to rely on transit
providers. They are configured on routers which may or may not be dedicated to
routing Internet traffic.

## In Peering Manager

Inside Peering Manager, you create Internet exchange peering sessions to model
BGP sessions established with remote peers and that are using Internet exchange
LANs. For each Internet exchange peering session that you create, the following
properties can be configured (n.b. some are optional):

  * `Autonomous System`: an autonomous system managed by a remote peer.
  * `Internet Exchange`: an Internet exchange providing a LAN and IP addresses
    for autonomous systems to peer.
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
  * `Import Routing Policies`: a list of routing policies to apply when
     receiving prefixes though the BGP session.
  * `Export Routing Policies`: a list of routing policies to apply when
     advertising prefixes though the BGP session.
  * `Comments`: text to explain the purposes of the BGP session. Can use
    Markdown formatting.
  * `Tags`: a list of tags to help identifying and searching for a BGP session.
