# Autonomous System

An autonomous system, also known as AS, is a collection of connected Internet
Protocol resources managed by network operators. It represents a single
administrative entity which has clearly identified routing policies.

An AS is defined mainly by its number, called the ASN. It is a 32-bit integer
(0 to 4294967295) unique to each autonomous system. Some numbers are reserved
for private use and must not be routed on the Internet.

## In Peering Manager

Inside Peering Manager, you create autonomous systems that you want to peer
with. Your own ASN numbers must be provided by checking the `affiliated`
field. For each AS that you create, the following properties can be configured
(n.b. some are optional):

* `ASN`: unique autonomous system number of the entity.
* `Name`: human-readable name attached to an AS.
* `Affiliated`: whether or not you manage said autonomous system.
* `IRR AS-SET`: the set of other ASNs that can be found behind this AS.
* `IPv6 Max Prefixes`: a zero or positive integer which defines the maximum
  number of IPv6 prefixes to receive from the AS.
* `IPv4 Max Prefixes`: a zero or positive integer which defines the maximum
  number of IPv4 prefixes to receive from the AS.
* `General Policy`: the General Peering Policy of an Autonomous System. This
  is auto synced from PeeringDB and is not user changeable.
* `Import Routing Policies`: a list of routing policies to apply when
   receiving prefixes from the AS.
* `Export Routing Policies`: a list of routing policies to apply when
   advertising prefixes to the AS.
* `Communities`: a list of communities to apply on prefixes received from or
  advertised by sessions with this AS.
* `Properties To Synchronise From PeeringDB`: some properties such as the
  name, the IRR AS-SET and prefix limits can be synchronised from the
  AS' [PeeringDB](https://peeringdb.com/) record.
* `Tags`: a list of tags to help identifying and searching for an AS.
* `Comments`: text to record some notes about the AS. Can use Markdown
  formatting.

Note that the best way to keep all of these properties up-to-date is to use the
PeeringDB integration that can synchronise some of them automatically.

The prefixes and the AS list resolved from the IRR AS-SET are cached in the
database and can be very large. Prefixes are stored as individual entries shared
between autonomous systems, so a prefix appearing in several AS-SETs is only kept
once; the `prefixes_updated` timestamp records when they were last refreshed. The
REST API does not include the prefixes and the AS list in autonomous system list
and detail responses by default; fetch them explicitly with the `fields` query
parameter (e.g. `?fields=asn,prefixes,as_list`) or through the
`/api/peering/autonomous-systems/{id}/as-set-prefixes` endpoint.
