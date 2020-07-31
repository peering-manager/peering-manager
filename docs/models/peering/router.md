# Router

A router is a network device which is designed to forward Internet Protocol
packets given a source and a destination addresses. It implements dynamic
routing protocols such as IS-IS, OSPF and BGP. This tool relies on the BGP
implementation of routers to track peers and sessions.

## In Peering Manager

Inside Peering Manager, you create routers and connect them to Internet
exchanges or assigned direct peering sessions to them. You'll then be able to
track on which router a BGP session is configured as well as add, change or
delete said session. For each router that you create, the following properties
are to be provided (some are however optional):

  * `Name`:
  * `Hostname`:
  * `Platform`:
  * `Encrypt Passwords`:
  * `Configuration Template`:
  * `NetBox Device`:
  * `Use NetBox`:
  * `NAPALM Username`:
  * `NAPALM Password`:
  * `NAPALM Timeout`:
  * `NAPALM Optional Arguments`:
  * `Comments`:
  * `Tags`:
