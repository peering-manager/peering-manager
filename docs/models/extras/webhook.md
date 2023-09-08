# Webhooks

Peering Manager can be configured to transmit outgoing webhooks to remote
systems in response to internal object changes.

Each webhook must be associated with at least one Peering Manager object type
and at least one event (create, update, or delete). Users can specify the
receiver URL, HTTP request type (`GET`, `POST`, etc.), content type, and
headers. A request body can also be specified; if left blank, this will
default to a serialized representation of the affected object.

!!! warning "Security Notice"
    Webhooks support the inclusion of user-submitted code to generate the URL,
    custom headers, and payloads, which may pose security risks under certain
    conditions. Only grant permission to create or modify webhooks to trusted
    users.

## Jinja2 Template Support

[Jinja2 templating](https://jinja.palletsprojects.com/) is supported for the
`URL`, `additional_headers` and `body_template` fields. This enables the user
to convey object data in the request headers as well as to craft a customized
request body. Request content can be crafted to enable the direct interaction
with external systems by ensuring the outgoing message is in a format the
receiver expects and understands.

For example, you might create a Peering Manager webhook to
[trigger a Slack message](https://api.slack.com/messaging/webhooks) any time
an IXP sessions is created. You can accomplish this using the following
configuration:

* Object type: Peering > Internet Exchange Peering Session
* HTTP method: `POST`
* URL: Slack incoming webhook URL
* HTTP content type: `application/json`
* Body template: `{"text": "IXP session {{ data['address'] }} was created by {{ username }}."}`

### Available Context

The following data is available as context for Jinja2 templates:

* `event` - The type of event which triggered the webhook: created, updated,
  or deleted.
* `model` - The NetBox model which triggered the change.
* `timestamp` - The time at which the event occurred (in
  [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format).
* `username` - The name of the user account associated with the change.
* `request_id` - The unique request ID. This may be used to correlate multiple
  changes associated with a single request.
* `data` - A detailed representation of the object in its current state. This
  is typically equivalent to the model's representation in Peering Manager's
  REST API.
* `snapshots` - Minimal "snapshots" of the object state both before and after
  the change was made; provided as a dictionary with keys named `prechange`
  and `postchange`. These are not as extensive as the fully serialized
  representation, but contain enough information to convey what has changed.

### Default Request Body

If no body template is specified, the request body will be populated with a
JSON object containing the context data. For example, a newly created site
might appear as follows:

```json
{
  "event": "create",
  "timestamp": "2023-08-07 19:30:23.140019+00:00",
  "model": "internetexchangepeeringsession",
  "username": "admin",
  "request_id": "af7aebe6-d049-405a-910f-d01e5ff043cd",
  "data": {
    "id": 85,
    "display": "S.H.I.E.L.D. Internet Exchange  - AS64498 - IP 2001:db8::fbf2:1",
    "service_reference": null,
    "autonomous_system": {
      "id": 9,
      "url": "/api/peering/autonomous-systems/9/",
      "display": "AS64498 - Stark Industris",
      "asn": 64498,
      "name": "Stark Industries",
      "ipv6_max_prefixes": 500,
      "ipv4_max_prefixes": 500
    },
    "ixp_connection": {
      "id": 1,
      "url": "/api/net/connections/1/",
      "display": "S.H.I.E.L.D. Internet Exchange",
      "name": "S.H.I.E.L.D. Internet Exchange",
      "mac_address": "1c:b8:5f:c0:d0:28",
      "ipv6_address": "2001:db8::fbf4:1/64",
      "ipv4_address": null
    },
    "ip_address": "2001:db8::fbf2:1",
    "status": {
      "value": "requested",
      "label": "Requested"
    },
    "password": null,
    "encrypted_password": null,
    "multihop_ttl": 1,
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
    "created": "2023-08-07T21:30:22.872649+02:00",
    "updated": "2023-08-07T21:30:22.872893+02:00"
  },
  "snapshots": {
    "prechange": null,
    "postchange": {
      "created": "2023-08-07T19:30:22.872Z",
      "updated": "2023-08-07T19:30:22.872Z",
      "local_context_data": null,
      "description": "",
      "comments": "",
      "service_reference": null,
      "autonomous_system": 2,
      "ip_address": "2001:db8::fbf2:1",
      "status": "requested",
      "password": null,
      "encrypted_password": null,
      "multihop_ttl": 1,
      "bgp_state": null,
      "received_prefix_count": 0,
      "advertised_prefix_count": 0,
      "last_established_state": null,
      "ixp_connection": 1,
      "is_route_server": false,
      "import_routing_policies": [],
      "export_routing_policies": [],
      "communities": [],
      "tags": []
    }
  }
}
```

## Conditional Webhooks

A webhook may include a set of conditional logic expressed in JSON used to
control whether a webhook triggers for a specific object. For example, you
may wish to trigger a webhook for devices only when the `status` field of an
object is "enabled":

```json
{
  "and": [
    {
      "attr": "status.value",
      "value": "enabled"
    }
  ]
}
```

Even though a webhook should fire when only one condition is triggered, the
condition must be included in a set, hence the `and` key in this example.

For more detail, see the reference documentation for Peering Manager's
[conditional logic](../../reference/conditions.md).

## Webhook Processing

When a change is detected, any resulting webhooks are placed into a Redis
queue for processing. This allows the user's request to complete without
needing to wait for the outgoing webhook(s) to be processed. The webhooks
are then extracted from the queue by the `rqworker` process and HTTP requests
are sent to their respective destinations. The current webhook queue and any
failed webhooks can be inspected in the admin UI under System > Background
Tasks.

A request is considered successful if the response has a 2XX status code;
otherwise, the request is marked as having failed. Failed requests may be
retried manually via the admin UI.

## Troubleshooting

To assist with verifying that the content of outgoing webhooks is rendered
correctly, Peering Manager provides a simple HTTP listener that can be run
locally to receive and display webhook requests. First, modify the target URL
of the desired webhook to `http://localhost:9000/`. This will instruct Peering
Manager to send the request to the local server on TCP port 9000. Then, start
the webhook receiver service from the Peering Manager root directory:

```no-highlight
$ python manage.py webhook_receiver
Listening on port http://localhost:9000. Stop with CONTROL-C.
```

You can test the receiver itself by sending any HTTP request to it. For example:

```no-highlight
$ curl -X POST http://localhost:9000 --data '{"foo": "bar"}'
```

The server will print output similar to the following:

```no-highlight
[1] Tue, 07 Apr 2020 17:44:02 GMT 127.0.0.1 "POST / HTTP/1.1" 200 -
Host: localhost:9000
User-Agent: curl/7.58.0
Accept: */*
Content-Length: 14
Content-Type: application/x-www-form-urlencoded

{"foo": "bar"}
------------
```

Note that `webhook_receiver` does not actually _do_ anything with the
information received: It merely prints the request headers and body for
inspection.

Now, when the Peering Manager webhook is triggered and processed, you should
see its headers and content appear in the terminal where the webhook receiver
is listening. If you don't, check that the `rqworker` process is running and
that webhook events are being placed into the queue (visible under the Peering
Manager admin UI).
