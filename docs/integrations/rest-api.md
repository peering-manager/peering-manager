# REST API Overview

## What is a REST API?

REST stands for [representational state
transfer](https://en.wikipedia.org/wiki/Representational_state_transfer). It's
a particular type of API which employs HTTP requests and [JavaScript Object
Notation (JSON)](https://www.json.org/) to facilitate create, retrieve,
update, and delete (CRUD) operations on objects within an application. Each
type of operation is associated with a particular HTTP verb:

* `GET`: Retrieve an object or list of objects
* `POST`: Create an object
* `PUT` / `PATCH`: Modify an existing object. `PUT` requires all mandatory
  fields to be specified, while `PATCH` only expects the field that is being
  modified to be specified.
* `DELETE`: Delete an existing object

Additionally, the `OPTIONS` verb can be used to inspect a particular REST API
endpoint and return all supported actions and their available parameters.

One of the primary benefits of a REST API is its human-friendliness. Because
it utilises HTTP and JSON, it's very easy to interact with Peering Manager
data on the command line using common tools. For example, we can get an IXP
BGP session from Peering Manager and output the JSON using `curl` and `jq`.
The following command makes an HTTP `GET` request for information about a
particular session, identified by its primary key, and uses `jq` to present
the raw JSON data returned in a more human-friendly format. (Piping the
output through `jq` isn't strictly required but makes it much easier to
read.)

```no-highlight
curl -s http://peering-manager/peering/internetexchangepeeringsessions/1234/ | jq '.'
```

```json
{
    "id": 1234,
    "display": "Some IX - AS64500 - IP 192.0.2.143",
    "service_reference": null,
    "autonomous_system": {
        "id": 8,
        "url": "http://localhost:8000/api/peering/autonomous-systems/254/",
        "display": "AS64500 - Some Network",
        "asn": 64500,
        "name": "Some Networks",
        "ipv6_max_prefixes": 10,
        "ipv4_max_prefixes": 100
    },
    "ixp_connection": {
        "id": 8,
        "url": "http://localhost:8000/api/net/connections/8/",
        "display": "Some IX",
        "name": "Some IX",
        "mac_address": null,
        "ipv6_address": null,
        "ipv4_address": "192.0.2.11/24"
    },
    "ip_address": "192.0.2.143",
    "status": {
        "value": "requested",
        "label": "Requested"
    },
    "password": null,
    "encrypted_password": null,
    "multihop_ttl": 1,
    "passive": false,
    "is_route_server": false,
    "import_routing_policies": [],
    "export_routing_policies": [],
    "communities": [],
    "local_context_data": null,
    "exists_in_peeringdb": false,
    "is_abandoned": false,
    "bgp_state": null,
    "received_prefix_count": 0,
    "advertised_prefix_count": 0,
    "last_established_state": null,
    "comments": "",
    "tags": [],
    "created": "2022-09-17T21:37:24.928949+02:00",
    "updated": "2022-09-18T10:37:40.249048+02:00"
}
```

Each attribute of the BGP sessions is expressed as an attribute of the JSON
object. Fields may include their own nested objects, as in the case of the
`connection` field above. Every object includes a primary key named `id` which
uniquely identifies it in the database.

## Interactive Documentation

Comprehensive, interactive documentation of all REST API endpoints is
available on a running Peering Manager instance at `/api/schema/swagger-ui/`.
This interface provides a convenient sandbox for researching and experimenting
with specific endpoints and request types. The API itself can also be explored
using a web browser by navigating to its root at `/api/`.

## Endpoint Hierarchy

Peering Manager's entire REST API is housed under the API root at
`https://<hostname>/api/`. The URL structure is divided at the root level by
application. Within each application exists a separate path for each model.
For example, the autonomous system and BGP group objects are located under the
"peering" application:

* `/api/peering/autonomous-systems/`
* `/api/peering/bgp-groups/`

Likewise, the email and contact objects are located under the "messaging"
application:

* `/api/messaging/contacts/`
* `/api/messaging/emails/`

The full hierarchy of available endpoints can be viewed by navigating to the
API root in a web browser.

Each model generally has two views associated with it: a list view and a
detail view. The list view is used to retrieve a list of multiple objects and
to create new objects. The detail view is used to retrieve, update, or delete
a single existing object. All objects are referenced by their numeric primary
key (`id`).

* `/api/peering/routers/` - List existing routers or create a new router
* `/api/peering/routers/123/` - Retrieve, update, or delete the router with
  ID 123

Lists of objects can be filtered using a set of query parameters. For example,
to find all connections belonging to the router with ID 123:

```
GET /api/net/connections/?router_id=123
```

See the [filtering documentation](../reference/filtering.md) for more details.

## Serialization

The REST API employs two types of serializers to represent model data: base
serializers and nested serializers. The base serializer is used to present the
complete view of a model. This includes all database table fields which
comprise the model, and may include additional metadata. A base serializer
includes relationships to parent objects, but **does not** include child
objects. For example, the `VLANSerializer` includes a nested representation its parent VLANGroup (if any), but does not include any assigned Prefixes.

```json
{
    "id": 456,
    "display": "",
    "name": "Baguettes Exchange",
    "peeringdb_netixlan": null,
    "status": {
        "value": "enabled",
        "label": "Enabled"
    },
    "vlan": 666,
    "mac_address": null,
    "ipv6_address": "2001:db8:13:37::1/64",
    "ipv4_address": "192.0.2.1/24",
    "internet_exchange_point": {
        "id": 7,
        "url": "http://peering-manager/api/peering/internet-exchanges/7/",
        "display": "Baguettes Exchange",
        "name": "Baguettes Exchange",
        "slug": "baguettes-exchange",
        "status": "enabled"
    },
    "router": null,
    "interface": "",
    "description": "",
    "local_context_data": null,
    "comments": "",
    "tags": [],
    "created": "2023-08-15T15:06:55.549195+02:00",
    "updated": "2023-09-26T18:26:14.927937+02:00"
},
```

### Related Objects

Related objects (e.g. `ForeignKey` fields) are represented using nested
serializers. A nested serializer provides a minimal representation of an
object, including only its direct URL and enough information to display the
object to a user. When performing write API actions (`POST`, `PUT`, and
`PATCH`), related objects may be specified by either numeric ID (primary key),
or by a set of attributes sufficiently unique to return the desired object.

For example, when creating a new direct session, its AS can be specified by
Peering Manager ID (PK):

```json
{
    "ip_address": "192.0.2.1",
    "autonomous_system": 123,
    ...
}
```

Or by a set of nested attributes which uniquely identifies the AS:

```json
{
    "ip_address": "192.0.2.1",
    "autonomous_system": {
        "asn": "64500"
    },
    ...
}
```

Note that if the provided parameters do not return exactly one object, a
validation error is raised.

### Brief Format

Most API endpoints support an optional "brief" format, which returns only a
minimal representation of each object in the response. This is useful when you
need only a list of available objects without any related data, such as when
populating a drop-down list in a form. As an example, the default (complete)
format of an autonomous system looks like this:

```
GET /api/peering/autonomous-systems/123/

{
    "id": 123,
    "display": "AS64498 - Stark Industries",
    "asn": 64498,
    "name": "Stark Industries",
    "comments": "",
    "irr_as_set": "MARVEL::STARK",
    "irr_as_set_peeringdb_sync": false,
    "ipv6_max_prefixes": 500,
    "ipv6_max_prefixes_peeringdb_sync": false,
    "ipv4_max_prefixes": 500,
    "ipv4_max_prefixes_peeringdb_sync": false,
    "import_routing_policies": [],
    "export_routing_policies": [],
    "communities": [],
    "prefixes": null,
    "affiliated": false,
    "local_context_data": null,
    "tags": [],
    "created": "2023-09-17T21:37:20.890016+02:00",
    "updated": "2023-09-20T00:33:35.521338+02:00"
}
```

The brief format is much more terse:

```
GET /api/peering/autonomous-systems/123/?brief=1

{
    "id": 123,
    "url": "http://peering-manager/api/peering/autonomous-systems/123/",
    "display": "AS64498 - Stark Industries",
    "asn": 64498,
    "name": "Stark Industries",
    "ipv6_max_prefixes": 500,
    "ipv4_max_prefixes": 500
}
```

The brief format is supported for both lists and individual objects.

## Pagination

API responses which contain a list of many objects will be paginated for
efficiency. The root JSON object returned by a list endpoint contains the
following attributes:

* `count`: The total number of all objects matching the query
* `next`: A hyperlink to the next page of results (if applicable)
* `previous`: A hyperlink to the previous page of results (if applicable)
* `results`: The list of objects on the current page

Here is an example of a paginated response:

```
HTTP 200 OK
Allow: GET, POST, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "count": 270,
    "next": "http://peering-manager/api/peering/autonomous-systems/?limit=50&offset=50",
    "previous": null,
    "results": [
        {
            "id": 54,
            "name": "Awesome Networks",
            ...
        },
        {
            "id": 56,
            "name": "MPLS Rules",
            ...
        },
        ...
    ]
}
```

The default page is determined by the
[`PAGINATE_COUNT`](../configuration/miscellaneous.md#paginate_count)
configuration parameter, which defaults to 50. However, this can be overridden
per request by specifying the desired `offset` and `limit` query parameters.
For example, if you wish to retrieve a hundred devices at a time, you would
make a request for:

```
http://peering-manager/api/peering/autonomous-systems/?limit=100
```

The response will return autonomous systems 1 through 100. The URL provided in
the `next` attribute of the response will return autonomous systems 101
through 200:

```json
{
    "count": 2861,
    "next": "http://peering-manager/api/peering/autonomous-systems/?limit=100&offset=100",
    "previous": null,
    "results": [...]
}
```

The maximum number of objects that can be returned is limited by the
[`MAX_PAGE_SIZE`](../configuration/miscellaneous.md#max_page_size)
configuration parameter, which is 1000 by default. Setting this to `0` or
`None` will remove the maximum limit. An API consumer can then pass `?limit=0`
to retrieve _all_ matching objects with a single request.

!!! warning
    Disabling the page size limit introduces a potential for very
    resource-intensive requests, since one API request can effectively
    retrieve an entire table from the database.

## Interacting with Objects

### Retrieving Multiple Objects

To query Peering Manager for a list of objects, make a `GET` request to the
model's _list_ endpoint. Objects are listed under the response object's
`results` parameter.

```no-highlight
curl -s -X GET http://peering-manager/api/peering/autonomous-systems/ | jq '.'
```

```json
{
  "count": 148,
  "next": "http://peering-manager/api/peering/autonomous-systems/?limit=50&offset=50",
  "previous": null,
  "results": [
    {
      "id": 53,
      "asn": 64500,
      ...
    },
    {
      "id": 54,
      "asn": 64501,
      ...
    },
    {
      "id": 55,
      "asn": 64502,
      ...
    },
    ...
  ]
}
```

### Retrieving a Single Object

To query Peering Manager for a single object, make a `GET` request to the
model's _detail_ endpoint specifying its unique numeric ID.

!!! note
    Note that the trailing slash is required. Omitting this will return a 302 redirect.

```no-highlight
curl -s -X GET http://peering-manager/api/peering/autonomous-systems/53/ | jq '.'
```

```json
{
  "id": 53,
  "asn": 64500,
  ...
}
```

### Creating a New Object

To create a new object, make a `POST` request to the model's _list_ endpoint
with JSON data pertaining to the object being created. Note that a REST API
token is required for all write operations; see the [authentication
section](#authenticating-to-the-api) for more information. Also be sure to set
the `Content-Type` HTTP header to `application/json`.

```no-highlight
curl -s -X POST \
-H "Authorization: Token $TOKEN" \
-H "Content-Type: application/json" \
http://peering-manager/api/peering/autonomous-systems/ \
--data '{"asn": 64535, "name": "Awesome Networks"}' | jq '.'
```

```json
{
  "id": 243,
  "display": "AS64535 - Awesome Networks",
  "asn": 64535,
  "name": "Awesome Networks",
  "comments": "",
  "irr_as_set": null,
  "irr_as_set_peeringdb_sync": true,
  "ipv6_max_prefixes": 0,
  "ipv6_max_prefixes_peeringdb_sync": true,
  "ipv4_max_prefixes": 0,
  "ipv4_max_prefixes_peeringdb_sync": true,
  "import_routing_policies": [],
  "export_routing_policies": [],
  "communities": [],
  "prefixes": null,
  "affiliated": false,
  "local_context_data": null,
  "tags": [],
  "created": "2022-10-15T21:35:43.646794+02:00",
  "updated": "2022-10-15T21:35:43.646807+02:00"
}
```

### Creating Multiple Objects

To create multiple instances of a model using a single request, make a `POST`
request to the model's _list_ endpoint with a list of JSON objects
representing each instance to be created. If successful, the response will
contain a list of the newly created instances. The example below illustrates
the creation of three new autonomous systems.

```no-highlight
curl -X POST -H "Authorization: Token $TOKEN" \
-H "Content-Type: application/json" \
-H "Accept: application/json; indent=4" \
http://peering-manager/api/peering/autonomous-systems/ \
--data '[
{"asn": 64531, "name": "Brand New Network AS1"},
{"asn": 64532, "name": "Brand New Network AS2"},
{"asn": 64533, "name": "Brand New Network AS3"}
]'
```

```json
[
    {
        "id": 21,
        "asn": 64531,
        ...
    },
    {
        "id": 22,
        "asn": 64532,
        ...
    },
    {
        "id": 23,
        "asn": 64533,
        ...
    }
]
```

### Updating an Object

To modify an object which has already been created, make a `PATCH` request to
the model's _detail_ endpoint specifying its unique numeric ID. Include any
data which you wish to update on the object. As with object creation, the
`Authorization` and `Content-Type` headers must also be specified.

```no-highlight
curl -s -X PATCH \
-H "Authorization: Token $TOKEN" \
-H "Content-Type: application/json" \
http://peering-manager/api/peering/autonomous-systems/243/ \
--data '{"irr_as_set": "RIPE::AS-AWESOME"}' | jq '.'
```

```json
{
  "id": 243,
  "display": "AS64535 - Awesome Networks",
  "asn": 64535,
  "name": "Awesome Networks",
  "comments": "",
  "irr_as_set": "RIPE::AS-AWESOME",
  "irr_as_set_peeringdb_sync": true,
  "ipv6_max_prefixes": 0,
  "ipv6_max_prefixes_peeringdb_sync": true,
  "ipv4_max_prefixes": 0,
  "ipv4_max_prefixes_peeringdb_sync": true,
  "import_routing_policies": [],
  "export_routing_policies": [],
  "communities": [],
  "prefixes": null,
  "affiliated": false,
  "local_context_data": null,
  "tags": [],
  "created": "2022-10-15T21:35:43.646794+02:00",
  "updated": "2022-10-15T21:41:12.247013+02:00"
}
```

!!! note "PUT versus PATCH"
    The Peering Manager REST API support the use of either `PUT` or `PATCH` to
    modify an existing object. The difference is that a `PUT` request requires
    the user to specify a _complete_ representation of the object being
    modified, whereas a `PATCH` request need include only the attributes that
    are being updated. For most purposes, using `PATCH` is recommended.

### Updating Multiple Objects

Multiple objects can be updated simultaneously by issuing a `PUT` or `PATCH`
request to a model's list endpoint with a list of dictionaries specifying the
numeric ID of each object to be deleted and the attributes to be updated. For
example, to update autonomous systems with IDs 10 and 11 to disable IPv4 max
prefix value synchronisation with PeeringDB, issue the
following request:

```no-highlight
curl -s -X PATCH \
-H "Authorization: Token $TOKEN" \
-H "Content-Type: application/json" \
http://peering-manager/api/peering/autonomous-systems/ \
--data '[
{"id": 10, "ipv4_max_prefixes_peeringdb_sync": false},
{"id": 11, "ipv4_max_prefixes_peeringdb_sync": false}
]'
```

Note that there is no requirement for the attributes to be identical among
objects. For instance, it's possible to update the status of one site along
with the name of another in the same request.

!!! note
    The bulk update of objects is an all-or-none operation, meaning that if
    Peering Manager fails to successfully update any of the specified objects 
    e.g. due a validation error), the entire operation will be aborted and
    none of the objects will be updated.

### Deleting an Object

To delete an object from Peering Manager, make a `DELETE` request to the
model's _detail_ endpoint specifying its unique numeric ID. The
`Authorization` header must be included to specify an authorization token,
however this type of request does not support passing any data in the body.

```no-highlight
curl -s -X DELETE \
-H "Authorization: Token $TOKEN" \
http://peering-manager/api/peering/autonomous-systems/243/
```

Note that `DELETE` requests do not return any data: If successful, the API
will return a 204 (No Content) response.

!!! note
    You can run `curl` with the verbose (`-v`) flag to inspect the HTTP
    response codes.

### Deleting Multiple Objects

Peering Manager supports the simultaneous deletion of multiple objects of the
same type by issuing a `DELETE` request to the model's list endpoint with a
list of dictionaries specifying the numeric ID of each object to be deleted.
For example, to delete autonomous systems with IDs 10, 11, and 12, issue the
following request:

```no-highlight
curl -s -X DELETE \
-H "Authorization: Token $TOKEN" \
-H "Content-Type: application/json" \
http://peering-manager/api/peering/autonomous-systems/ \
--data '[{"id": 10}, {"id": 11}, {"id": 12}]'
```

!!! note
    The bulk deletion of objects is an all-or-none operation, meaning that if
    Peering Manager fails to delete any of the specified objects (e.g. due a
    dependency by a related object), the entire operation will be aborted and
    none of the objects will be deleted.

## Authentication

The Peering Manager REST API primarily employs token-based authentication. For
convenience, cookie-based authentication can also be used when navigating the
browsable API.

### Tokens

A token is a unique identifier mapped to a Peering Manager user account. Each
user may have one or more tokens which he or she can use for authentication
when making REST API requests. To create a token, navigate to the API tokens
page under your user profile.

Each token contains a 160-bit key represented as 40 hexadecimal characters.
When creating a token, you'll typically leave the key field blank so that a
random key will be automatically generated. However, Peering Manager allows
you to specify a key in case you need to restore a previously deleted token to
operation.

Additionally, a token can be set to expire at a specific time. This can be
useful if an external client needs to be granted temporary access to Peering
Manager.

### Restricting Write Operations

By default, a token can be used to perform all actions via the API that a user
would be permitted to do via the web UI. Deselecting the "write enabled"
option will restrict API requests made with the token to read operations (e.g.
GET) only.

### Authenticating to the API

An authentication token is attached to a request by setting the
`Authorization` header to the string `Token` followed by a space and the
user's token:

```
$ curl -H "Authorization: Token $TOKEN" \
-H "Accept: application/json; indent=4" \
https://peering-manager/api/peering/autonomous-systems/
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [...]
}
```

A token is not required for read-only operations when using the
[`LOGIN_REQUIRED`](../configuration/security.md#login_required) configuration
parameter. However, if a token _is_ required but not present in a request, the
API will return a 403 (Forbidden) response:

```
$ curl https://peering-manager/api/peering/autonomous-systems/
{
    "detail": "Authentication credentials were not provided."
}
```

## HTTP Headers

### `API-Version`

This header specifies the API version in use. This will always match the
version of Peering Manager installed. For example, Peering Manager v1.8.2 will
report an API version of `1.8`.

### `X-Request-ID`

This header specifies the unique ID assigned to the received API request. It
can be very handy for correlating a request with change records. For example,
after creating several new objects, you can filter against the object changes
API endpoint to retrieve the resulting change records:

```
GET /api/core/object-changes/?request_id=6fc8a28c-83f0-4d88-a017-3d44de9046ee
```

The request ID can also be used to filter many objects directly, to return
those created or updated by a certain request:

```
GET /peering/autonomous-systems/?created_by_request=6fc8a28c-83f0-4d88-a017-3d44de9046ee
```

!!! note
    This header is included with _all_ Peering Manager responses, although it
    is most practical when working with an API.
