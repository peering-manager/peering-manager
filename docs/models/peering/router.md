# Router

A router is a network device which is designed to forward Internet Protocol
packets given a source and a destination addresses. It implements dynamic
routing protocols such as IS-IS, OSPF and BGP. This tool relies on the BGP
implementation of routers to track peers and sessions.

## In Peering Manager

Inside Peering Manager, you create routers and connect them to Internet
exchanges, and/or assign direct peering sessions to them. You'll then be able to
track on which router a BGP session is configured as well as add, change or
delete said session. For each router that you create, the following properties
can be configured (n.b. some are optional):

  * `Local Autonomous System`: autonomous system to which the router belongs.
  * `Name`: human-readable name attached to a router.
  * `Hostname`: resolvable FQDN or an IP address to reach the router.
  * `Platform`: network operating system which is running on the router.
  * `Encrypt Passwords`: an option to tell if protected BGP sessions use
    encrypted passwords and if Peering Manager should generate and record the
    encrypted password if it can.
  * `Configuration Template`: a template used generate the configuration of the
    router.
  * `NetBox Device`: an valid ID inside a NetBox instance where the router is
    also referenced.
  * `Use NetBox`: an option to use NetBox NAPALM capabilities to reach the
    router. Features requiring NAPALM will use NetBox API as a proxy.
  * `NAPALM Username`: a username for Peering Manager to use for connecting to
    the router. It overrides the `NAPALM_USERNAME` global setting.
  * `NAPALM Password`: a password for Peering Manager to use for connecting to
    the router. It overrides the `NAPALM_PASSWORD` global setting.
  * `NAPALM Timeout`: a timeout for Peering Manager to use for connecting to
    the router. It overrides the `NAPALM_TIMEOUT` global setting.
  * `NAPALM Optional Arguments`: optional arguments for Peering Manager to use
    for connecting to the router. It overrides the `NAPALM_ARGS` global
    setting. If you see connection issues with some routers, try setting
    `{"fast_cli": false}` as value for these args.
  * `Comments`: text to record some notes about the router. Can use Markdown
    formatting.
  * `Tags`: a list of tags to help identifying and searching for a router.
