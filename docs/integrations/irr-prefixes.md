# Prefix Lists And AS Lists From IRR Objects

Each AS can originate or advertise routes depending on prefixes assigned to it
and the relationship it has with other networks. For instance, a network
service provider selling transit to its customers will re-advertise the routes
of its customers back to other networks it is peering with. It will also most
likely advertise its own routes.

For security reasons, autonomous systems tend to setup BGP filters with prefix
lists and allowed AS paths to prevent them from learning routes advertised by
peers which are not supposed to. To know which prefix an AS is allowed to
advertise, networks use Internet Routing Registries (IRR) and the objects they
hold.

Networks that are used to peer with other networks usually publish AS-SET
objects. These objects define which other AS-SETs or autonomous systems a
network will probably advertise. These objects can be translated into prefix
lists by using tools such as [bgpq3](https://github.com/snar/bgpq3) and
[bgpq4](https://github.com/bgp/bgpq4).

Peering Manager can use bgpq3/bpgq4 to fetch prefix lists in a JSON format to
store them in its database and/or to provide them within the templating
engine. One of the mentioned tools must be installed on the same host and the
[BGPQ3_PATH](../configuration/tools.md#bgpq3_path) value must be set. It is
possible to influence the way bgpq3/bgpq4 is going to be called by changing
the [BGPQ3_ARGS](../configuration/tools.md#bgpq3_args) value.

To resolve autonomous system or AS-SET into a prefix list or an AS list,
bgpq3/bgpq4 needs to query a host and to ask for values found in one or more
sources. Both of these parameters can be tweaked by changing
[BGPQ3_HOST](../configuration/tools.md#bgpq3_host) and
[BGPQ3_SOURCES](../configuration/tools.md#bgpq3_sources) respectively.

When bgpq4 is used as a tool to fetch IRR objects, Peering Manager is able to
leverage bgpq4 capability to identify the source of an AS-SET if it is
prefixed with one like `RIPE::AS201281:AS-MAZOYER-EU`. bgpq4 will look for the
`::` and identify the root source to use. By default, this feature is disabled
by Peering Manager, but it needs to be enabled, this can be done by setting
[BGPQ4_KEEP_SOURCE_IN_SET](../configuration/tools.md#bgpq4_keep_source_in_set)
value to `True` in the configuration.

!!! warning
    `get_irr_data` replaces `grab_prefixes`. While `grab_prefixes` still
    works, it is deprecated and will be removed in a future version.

To store prefixes and AS lists in the database, Peering Manager provides a
command. It can be run regularly, like housekeeping. It will take care of
fetching the prefixes for both IPv4 and IPv6 address families as well as the
AS list for each autonomous system.

```no-highlight
# venv/bin/python3 manage.py get_irr_data
```

History is not kept when it comes to prefixes. It means that each run of this
command will override known prefixes and replace them with the new ones.

Building prefix list with hundreds of thousands lines can be quite time
consuming and sometimes even useless. For example, if you have a transit
provider advertising a full routing table, keeping a prefix list for this AS
does not always make sense. To avoid caching prefix list that are too long,
the `--limit=N` parameter can be passed to the command, which, as a result,
will not store prefix lists exceeding _N_ prefixes.

```no-highlight
# venv/bin/python3 manage.py get_irr_data --limit=1000
```
