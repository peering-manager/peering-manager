# Peering Portal API

Peering Manager exposes a dedicated API surface at `/api/peering/portal/`
designed to be consumed by an external "peering portal": a public-facing
website that lets other networks request BGP peering with the AS operating
Peering Manager.

The portal API is limited to portal-specific operations: looking up a
requesting network, discovering common peering locations, submitting a
peering request, and tracking the status of past requests. Operator
decisions (accept and reject) and listing of established BGP sessions are
served by the standard REST API.

This page describes how a custom portal interacts with Peering Manager. The
design follows the IETF draft
[draft-ramseyer-grow-peering-api](https://datatracker.ietf.org/doc/draft-ramseyer-grow-peering-api/)
where compatible.

## Glossary

| Term                       | Meaning                                                                                                                                                                                                                   |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Affiliated AS**          | The autonomous system the Peering Manager operator runs and accepts peering for. Selected per-user in the top-right menu ("Select affiliated AS").                                                                        |
| **Peer AS** / **Local AS** | The external network asking to peer. In submission payloads this is `local_asn` (it is local from the requesting portal user's perspective).                                                                              |
| **Requesting ASN**         | Same as Peer AS, used in URL and query parameters as `asn`.                                                                                                                                                               |
| **Peering request**        | A submission from an external network, identified by a UUID `request_id`.                                                                                                                                                 |
| **Requested session**      | One BGP session entry inside a peering request, identified by `session_id`.                                                                                                                                               |
| **Tracking ID**            | The UUID (`request_id`) that the portal hands back to the requester so they can poll status or cancel without authentication.                                                                                             |
| **Local IP / Peer IP**     | Inside a session payload, `local_ip` is the requesting network's IP and `peer_ip` is the operator's IP on the connection. The pair `(peer_ip, location)` uniquely identifies which operator connection a session targets. |
| **Location**               | Either an IXLan (public peering, format `pdb:ix:<ixlan_id>`) or a PeeringDB facility (private peering, format `<facility_id>`).                                                                                           |

## Architecture Overview

A typical deployment looks like this:

```text
+-----------------+         +-------------------+        +-----------------+
|   End user      | <-----> |  Peering portal   | <----> | Peering Manager |
|  (web browser)  |  HTML   | (your custom app) |  REST  |     (this app)  |
+-----------------+         +-------------------+        +-----------------+
                                       |
                                       | reads PeeringDB cache,
                                       | writes peering requests,
                                       | reads existing sessions
```

The portal sits between the end user and Peering Manager:

* The **end user** never talks to Peering Manager directly.
* The **portal** holds the Peering Manager API token and forwards requests on
  behalf of users.
* The **operator** reviews requests through Peering Manager's standard UI or
  REST API.

The portal authenticates to Peering Manager with a single API token, so do
not embed that token in client-side code. The portal must proxy requests
server-side and keep the token secret.

## Authentication and Permissions

All portal API endpoints require a Peering Manager API token authenticated
via the `Authorization: Token <key>` HTTP header.

The user account that owns the token needs:

1. Both the *Add peering request* and *Change peering request* permissions.
2. An affiliated AS selected from the top-right user menu. The portal API
   uses this AS as the peer side (the AS that the external network is
   asking to peer with) and scopes every query to it. Requests targeting
   any other affiliated AS are not visible to this token.

If a portal endpoint is called by a token whose owner has no affiliated AS
set, it returns a HTTP 503 with an explicit error message.

The portal can ask Peering Manager which AS the token is bound to:

```bash
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    "$PM_API_URL/peering/portal/affiliated"
```

```json
{"asn": 64496, "name": "Example"}
```

This is useful for showing the user "you are peering with AS64496" without
hard-coding it on the portal side.

!!! warning "ASN ownership is the portal's responsibility"
    Peering Manager authenticates the portal as a whole via a single API
    token. It has no notion of which end user is making a particular call
    and does not verify that the ASN supplied in a request actually belongs
    to the requesting user. Every request that reaches Peering Manager
    looks like it came from the portal itself.

    The portal must verify that a user is authorised to act on behalf of
    the ASN they claim before forwarding any submission, cancellation, or
    status lookup. Without this check, any visitor could file or cancel
    peering requests on behalf of an arbitrary network.

    The recommended way is to delegate authentication to PeeringDB:

    * Use [PeeringDB OAuth](https://docs.peeringdb.com/oauth/) to log the
      user in. The OAuth flow returns the PeeringDB user account, which
      lists the networks (ASNs) that user is affiliated with on PeeringDB.
    * Restrict every request operation in the portal to ASNs that appear
      in the authenticated user's affiliations.

## Example Portal Workflow

Below is a walkthrough for a simple portal that lets a user submit a peering
request (over an IXP or in a private facility), look up past requests, and
view existing peering sessions. All examples use `curl` for clarity, but any
HTTP client will work.

### Step 1, look up the requesting network

The portal asks the user to enter the ASN of their network. That ASN must
have a record in the local PeeringDB cache, otherwise no information can be
retrieved and no common locations can be computed.

```bash
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    "$PM_API_URL/peering/portal/network/64500"
```

```json
{
  "asn": 64500,
  "name": "Example Network",
  "name_long": "Example Network Inc.",
  "info_prefixes4": 100,
  "info_prefixes6": 50,
  "irr_as_set": "AS-EXAMPLE",
  "policy_general": "Open",
  "contacts": [
    {"name": "NOC", "email": "noc@example.net", "role": "Technical"}
  ]
}
```

The portal can use this response to pre-fill the request form (network
name, maximum prefix counts, contact email).

A HTTP 404 response means the ASN is not present in the PeeringDB cache.

### Step 2, discover common peering locations

Once the ASN is validated, the portal asks Peering Manager which IXPs and
facilities are shared between the requester and the affiliated AS:

```bash
# All locations (IXPs + facilities)
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    "$PM_API_URL/peering/portal/locations?asn=64500"

# IXPs only
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    "$PM_API_URL/peering/portal/locations?asn=64500&location_type=public"

# Facilities only (for private peering)
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    "$PM_API_URL/peering/portal/locations?asn=64500&location_type=private"
```

```json
{
  "peer_asn": 64496,
  "locations": [
    {
      "location": "pdb:ix:42",
      "name": "Example IX",
      "peering_type": "public",
      "sessions": [
        {
          "local_ip": "192.0.2.1/24",
          "peer_ip": "192.0.2.254/24",
          "address_family": 4,
          "existing": false
        },
        {
          "local_ip": "192.0.2.1/24",
          "peer_ip": "192.0.2.253/24",
          "address_family": 4,
          "existing": false
        },
        {
          "local_ip": "2001:db8::1/64",
          "peer_ip": "2001:db8::ffff/64",
          "address_family": 6,
          "existing": false
        }
      ]
    },
    {
      "location": "17",
      "name": "Example Facility",
      "peering_type": "private",
      "sessions": []
    }
  ]
}
```

For each public location, `sessions` lists possible BGP sessions based on
the requester's PeeringDB presence. The `existing` flag means a session
with that IP is already configured in Peering Manager.

A BGP session is uniquely identified by the pair *(peer IP, operator
connection)*. One peer IP can pair with several operator connections on the
same IX (multi-router setups), and a peer can also have several IPs on the
same IXLan, so `sessions` is the cartesian product of those two axes per
address family: one row per pair. Rows are emitted only when at least one
operator connection exists for the address family.

`local_ip` values come from PeeringDB host records, returned with the
matching IXLan prefix length appended (for example `192.0.2.1/24`) so they
are directly usable as BGP session IP fields. `peer_ip` is the operator IP
for that specific pair.

When the portal submits, each session entry includes `local_ip`, `peer_ip`,
and `location`. That triple unambiguously identifies one operator
connection.

For private locations, the user enters both IP addresses themselves (the
PeeringDB cache does not know which IPs are negotiated on a private
interconnect): `local_ip` for their own end, `peer_ip` for the operator's
end. Both are required at submission time, because the operator-side IP
on a private link cannot be guessed from anything else except trivial
/31 or /127 cases. The `location` value for a facility is its numeric
PeeringDB ID as a string (for example `"17"`).

### Step 3, submit the peering request

Once the user picks the locations and (optionally) provides session
parameters, the portal submits the request:

```bash
# Public peering (IXP) example
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    -H "Content-Type: application/json" \
    -X POST "$PM_API_URL/peering/portal/sessions" \
    -d '{
      "local_asn": 64500,
      "peer_type": "public",
      "email": "noc@example.net",
      "sessions": [
        {"local_ip": "192.0.2.1/24", "peer_ip": "192.0.2.254",
         "location": "pdb:ix:42"},
        {"local_ip": "2001:db8::1/64", "peer_ip": "2001:db8::ffff",
         "location": "pdb:ix:42", "session_secret": "s3cret"}
      ]
    }'
```

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "sessions_count": 2
}
```

`peer_ip` is matched on host address only, so both bare IPs
(`192.0.2.254`) and IPs with prefix length (`192.0.2.254/24`) are accepted.

A private peering request looks the same except `peer_type` is `"private"`
and `location` carries the facility ID (as returned in the `locations`
field of the location lookup):

```bash
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    -H "Content-Type: application/json" \
    -X POST "$PM_API_URL/peering/portal/sessions" \
    -d '{
      "local_asn": 64500,
      "peer_type": "private",
      "email": "noc@example.net",
      "sessions": [
        {
          "local_ip": "192.0.2.10/30",
          "peer_ip": "192.0.2.9/30",
          "location": "17"
        }
      ]
    }'
```

The response contains a `request_id`, a UUID acting as the public-facing
tracking identifier.

!!! note
    Submitting a request does not create any BGP sessions or
    `AutonomousSystem` records in Peering Manager. Those are only created
    if the operator accepts the request (see
    [Operator decisions](#operator-decisions) below).

The submission is rejected with a HTTP 409 in two cases:

* **Pending duplicate**: the requester already has a pending peering
  request that contains one of the submitted IPs:

    ```json
    {
      "detail": "Duplicate request: sessions with these IPs are already pending.",
      "overlapping_ips": ["192.0.2.1/24"]
    }
    ```

* **Existing session conflict**: one of the submitted sessions matches a
  BGP session already configured in Peering Manager (same
  `(operator connection, IP)` for public peering, or same `(peer ASN, IP)`
  for private peering):

    ```json
    {
      "detail": "Sessions with these IPs are already configured.",
      "existing_session_ips": ["192.0.2.1/24"]
    }
    ```

### Step 4, show the user their past requests

Because the portal is stateless on the server side, past requests are
discovered via the tracking IDs. For each known tracking ID, the portal
queries:

```bash
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    "$PM_API_URL/peering/portal/sessions/550e8400-e29b-41d4-a716-446655440000"
```

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "peer_type": "public",
  "local_asn": 64500,
  "peer_asn": 64496,
  "decision_comment": "",
  "sessions": [
    {
      "session_id": 12,
      "local_ip": "192.0.2.1/24",
      "peer_ip": "192.0.2.254/24",
      "location": "pdb:ix:42",
      "location_name": "Example IX",
      "status": "accepted",
      "rejection_comment": ""
    },
    {
      "session_id": 13,
      "local_ip": "2001:db8::1/64",
      "peer_ip": "2001:db8::ffff/64",
      "location": "pdb:ix:42",
      "location_name": "Example IX",
      "status": "rejected",
      "rejection_comment": "Auto-rejected: A session with IP 2001:db8::1/64 already exists on Example IX."
    }
  ],
  "created": "2026-04-22T08:30:00Z",
  "updated": "2026-04-22T10:15:00Z"
}
```

A HTTP 404 response is intentionally generic so that an attacker guessing
tracking IDs cannot enumerate other users' requests.

### Step 5, cancel a pending request

While a request is still `pending`, the user can cancel it:

```bash
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    -X DELETE \
    "$PM_API_URL/peering/portal/sessions/550e8400-e29b-41d4-a716-446655440000"
```

A HTTP 204 response means the request and all its pending sessions were marked
as cancelled. A HTTP 409 response means the request had already been accepted
or refused, so there is nothing to cancel. A HTTP 404 is returned for an
unknown tracking ID (same anti-enumeration behaviour as the status endpoint).

### Step 6, list existing peering sessions

The portal API itself does not expose established BGP sessions because they
are operator-managed objects. To list them, use the standard REST API:

```bash
# All IXP sessions for a given ASN
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    "$PM_API_URL/peering/internet-exchange-peering-sessions/?autonomous_system_asn=64500"

# All direct (private) sessions for a given ASN
curl -s -H "Authorization: Token $PM_API_TOKEN" \
    "$PM_API_URL/peering/direct-peering-sessions/?autonomous_system_asn=64500"
```

Each session response includes its current `status` (`requested`,
`provisioning`, `enabled`, `disabled`, etc.) and operational `bgp_state`
(`idle`, `established`, etc.) when polled. The portal can present these
alongside the user's own requests so the user has a single view of what is
already configured and what they are asking for.

See the [REST API Overview](rest-api.md) for the full session schema.

## Operator Decisions

Once a request is submitted, an operator reviews it through Peering
Manager's web UI (under "Peering Requests") or via the REST API.

These actions are not part of the portal API surface. They are meant for
the operator and require the *Review peering requests* permission, which is
distinct from the *Add* / *Change* permissions the portal token holds.

### What happens on accept

When the operator accepts a request:

* The requesting `AutonomousSystem` record is automatically created from
  PeeringDB data (name, IRR AS-SET, max prefix counts) if it does not
  already exist. If the requesting ASN has no PeeringDB record, the
  affected sessions are auto-rejected with a comment.
* For private peering requests, the operator must set a `relationship` on
  the request before accepting it. Otherwise the accept call returns
  an error.
* For each accepted session, a BGP session is created with the initial
  status defined by the
  [`PEERING_REQUEST_SESSION_STATUS`](../configuration/miscellaneous.md#peering_request_session_status)
  setting.
* If the requester supplied a `session_secret`, it becomes the BGP session
  password.
* For accepted private peering sessions, the `peer_ip` supplied by the
  requester is set as the operator-side local IP on the created direct
  session, so the operator does not have to fill it in by hand.
* Sessions that can no longer be created (for example, because the operator
  has manually configured a conflicting session in the meantime, or no IXP
  connection with a matching address family is configured) are
  automatically marked as `rejected` with an explanatory comment.

### Avoiding out-of-band conflicts

By default, manually creating a BGP session whose IP matches a pending
peering request only logs a warning. To make Peering Manager refuse such
creations outright (so an operator cannot accidentally configure a session
while the corresponding request is still awaiting review), enable the
[`PEERING_REQUEST_BLOCKS_SESSION_CREATION`](../configuration/miscellaneous.md#peering_request_blocks_session_creation)
setting.

## Reference Implementation Hints

A minimal portal implementation only needs to:

1. Settings to provide the Peering Manager URL and API token to use, the
   affiliated ASN will be infered from an API call on
   `/api/peering/portal/affiliated`.
2. A way to surface ASN entry, location selection and session selection to a
   user.
3. A way to display existing peering requests and sessions by using tracking
   IDs.

All server-side state lives in Peering Manager, so the portal can be deployed
as a stateless container.

## Endpoint Reference

| Method   | Path                                                                     | Purpose                                                             |
|----------|--------------------------------------------------------------------------|---------------------------------------------------------------------|
| `GET`    | `/api/peering/portal/affiliated`                                         | Return the affiliated AS bound to the calling token (`asn`, `name`) |
| `GET`    | `/api/peering/portal/network/{asn}`                                      | Look up a network by ASN in the PeeringDB cache                     |
| `GET`    | `/api/peering/portal/locations?asn={asn}&location_type={public,private}` | List shared IXPs and/or facilities                                  |
| `POST`   | `/api/peering/portal/sessions`                                           | Submit a peering request                                            |
| `GET`    | `/api/peering/portal/sessions/{request_id}`                              | Get the status of a request                                         |
| `DELETE` | `/api/peering/portal/sessions/{request_id}`                              | Cancel a pending request                                            |

All endpoints return JSON. Errors follow Django REST Framework conventions
with a top-level `detail` field describing the problem.
