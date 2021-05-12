# Config Contexts

Config(uration) contexts can be used to give "context" (or "hints") to tooling
that uses Peering Manager as its data source. This context is given as a simple
JSON snippet, which is able to model properties that Peering Manager by default
would not be able to represent.

## Config Contexts for Routers

In case of routers, this field can be leveraged in a similar manner as in other
network source-of-truth tools, such as Nautobot or NetBox. However, in Peering
Manager, this JSON field can be used to model explicitly BGP-related
properties, such as communities associated with the router.

For example, the simple JSON snippet below would designate the `bgp_region`
of the router.

```
{
    "bgp_region": "eu-frankfurt",
}
```

This example config context is exposed in the API within the router item, in
the following manner:

```
{
    ...
    "results": [
        {
            "id": 1,
            ...
            "config_context": {
                "bgp_region": "eu-frankfurt",
            }
        }
    ]
}
```

## Config Contexts for Routing Policies

Routing policies can be sometimes more tricky than just applying a policy, or
not, to a given BGP session(s). In the case presented below, a few prefixes
are depreferenced in the associated BGP session(s).

```
{
    "depreference_prefixes": [
        "192.0.2.0/24",
        "198.51.100.0/24"
    ]
}
```

Config contexts also allow the easy injection of arbitrary variables into
your tooling, saving you from having to associate each routing policy 
with an action to perform or preference to save.

```
{
    "aspath_filter_in": "AS64500:JUST-THE-GOOD-PARTS"
}
...
{
    "originate_default_route": true,
    "allow_private_as": true
}
```

