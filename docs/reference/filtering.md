# REST API Filtering

## Filtering Objects

The objects returned by an API list endpoint can be filtered by attaching one
or more query parameters to the request URL. For example,
`GET /api/peering/internet-exchanges/?status=enabled` will return only IXPs
with a status of "enabled".

Multiple parameters can be joined to further narrow results. For example,
`GET /api/peering/internet-exchanges/?status=enabled&local_autonomous_system_id=1`
will return only active IXPs for the autonomous system having ID 1.

Generally, passing multiple values for a single parameter will result in a
logical OR operation. For example,
`GET /api/peering/internet-exchanges/?status=enabled&status=disabled` will
return IXPs which are enabled or disabled. However, a logical AND operation
will be used in instances where a field may have multiple values, such as
tags. For example, `GET /api/peering/internet-exchanges/?tag=foo&tag=bar` will
return only sites which have both the "foo" _and_ "bar" tags applied.

### Filtering by Choice Field

Some models have fields which are limited to specific choices, such as the
`status` field on the IXP model. To find all available choices for this field,
make an authenticated `OPTIONS` request to the model's list endpoint, and use
`jq` to extract the relevant parameters:

```no-highlight
$ curl -s -X OPTIONS \
-H "Authorization: Token $TOKEN" \
-H "Content-Type: application/json" \
http://peering-manager/api/peering/internet-exchanges/ | jq ".actions.POST.status.choices"
[
  {
    "value": "enabled",
    "display_name": "Enabled"
  },
  {
    "value": "pre-maintenance",
    "display_name": "Pre-maintenance"
  },
  {
    "value": "maintenance",
    "display_name": "Maintenance"
  },
  {
    "value": "post-maintenance",
    "display_name": "Post-maintenance"
  },
  {
    "value": "disabled",
    "display_name": "Disabled"
  }
]
```

!!! note
    The above works only if the API token used to authenticate the request has
    permission to make a `POST` request to this endpoint.

## Lookup Expressions

Certain model fields also support filtering using additional lookup
expressions. This allows for negation and other context-specific filtering.

These lookup expressions can be applied by adding a suffix to the desired
field's name, e.g. `mac_address__n`. In this case, the filter expression is
for negation and it is separated by two underscores. Below are the lookup
expressions that are supported across different field types.

### Numeric Fields

Numeric based fields (ASN, VLAN ID, etc) support these lookup expressions:

| Filter  | Description              |
|---------|--------------------------|
| `n`     | Not equal to             |
| `lt`    | Less than                |
| `lte`   | Less than or equal to    |
| `gt`    | Greater than             |
| `gte`   | Greater than or equal to |
| `empty` | Is empty/null (boolean)  |

Here is an example of a numeric field lookup expression that will return all
autonomous systems with an ASN greater than 100:

```no-highlight
GET /api/peering/autonomous-systems/?asn__gt=100
```

### String Fields

String based (char) fields (name, description, etc) support these lookup
expressions:

| Filter  | Description                            |
|---------|----------------------------------------|
| `n`     | Not equal to                           |
| `ic`    | Contains (case-insensitive)            |
| `nic`   | Does not contain (case-insensitive)    |
| `isw`   | Starts with (case-insensitive)         |
| `nisw`  | Does not start with (case-insensitive) |
| `iew`   | Ends with (case-insensitive)           |
| `niew`  | Does not end with (case-insensitive)   |
| `ie`    | Exact match (case-insensitive)         |
| `nie`   | Inverse exact match (case-insensitive) |
| `empty` | Is empty/null (boolean)                |

Here is an example of a lookup expression on a string field that will return
all autonomous systems with `RIPE` in the IRR AS-SET:

```no-highlight
GET /api/peering/autonomous-systems/?irr_as_set__ic=RIPE
```

### Foreign Keys & Other Fields

Certain other fields, namely foreign key relationships support just the
negation expression: `n`. Here is an example of a lookup expression on a 
oreign key, it would return all connections that don't have an IXP ID of 7:

```no-highlight
GET /api/net/connections/?internet_exchange_point_id__n=7
```

## Ordering Objects

To order results by a particular field, include the `ordering` query
parameter. For example, order the list of autonomous systems according to
their ASN values:

```no-highlight
GET /api/peering/autonomous-systems/?ordering=asn
```

To invert the ordering, prepend a hyphen to the field name:

```no-highlight
GET /api/peering/autonomous-systems/?ordering=-asn
```

Multiple fields can be specified by separating the field names with a comma. For example:

```no-highlight
GET /api/peering/autonomous-systems/?ordering=name,-asn
```
