## Version 1.10.3 | MARK I (Bug fixes release) | 2026-02-05

> [!NOTE]
> Password hashes encrypted with the Juniper Junos cipher may change upon re-encryption. This is because the cipher now uses the remote neighbor IP address as a salt during hashing. After re-encryption, password hashes for Juniper Junos devices should remain consistent, preventing unnecessary configuration differences in the future.

### Enhancements

* Add `relationships` Jinja2 filter, to get a list of relationships for an autonomous
system
* Add `strip_irr_sources` Jinja2 filter, get a list of AS-SET with each item stripped of its source prefix
* Global refactoring of password encryption logic
* Add Arista password encryption/decryption and migrate existing platform to use it
* Adjust Juniper password encryption logic to use a salt based on the remote neighbor IP
* Add tooltip to AS synchronise button
* Slight tweak for PeeringDB tooltips in AS view

### Bug Fixes

* Fix changing affiliated AS via top bar dropdown
* Fix PeeringDB cache flush with existing hidden peers objects, objects will also be restored after re-building the PeeringDB cache

## Version 1.10.2 | MARK I (Bug fixes release) | 2025-12-23

### Enhancements

* [#914](https://github.com/peering-manager/peering-manager/issues/914) Add a view to see prefixes for an AS
* Improve shared IXP query performance
* Add created/update date and time under a dropdown in object tabs
* Rework user preferences view to be able to change preferences
* Add `last_used` and `allowed_ips` fields for tokens
* Use date and time picker where appropriate

### Bug Fixes

* Fix exception for orphaned IXP sessions
* Fix URL for messaging views, they are now all nested under `/messaging/`
* Normalise text when no routing policies are assigned to an object
* Fix connection view for router not having bulk action buttons
* Fix fields not being validated when saving the BGP state of sessions
* Fix journal entries bulk edit view
* Allow picking a date and time in the past (needed for filter forms)

### Code Housekeeping / Code Quality

* Support poetry 2.x and uv

### Documentation

* Fix mention of PostgreSQL version (by @henriklb)

## Version 1.10.1 | MARK I (Bug fixes release) | 2025-12-01

### Bug Fixes

* Fix global search page that failed to render properly
* Fix IRR data no properly gathered if the prefix list for either IPv6 or IPv4 was empty
* Improve `get_irr_data` command to avoid early exits if prefix lists for an AS failed to be retrieved

## Version 1.10.0 | MARK I (Features release) | 2025-11-29

The 1.10.x releases require Python 3.10 or later as well as PostgreSQL 14 or later.

### API Breaking Changes

* Rename IX-API `url` field to `api_url`
* The `Community` model has been moved from the `peering` app to `bgp`. Accordingly, its REST API endpoint has been moved from `/api/peering/communities/` to `/api/bgp/communities/`
* The `routing_policies` variable of configuration template now returns routing policies to be set on the router instead of all recorded routing policies

### New Features

#### Support `fields` and `exclude` API query parameters ([#942](https://github.com/peering-manager/peering-manager/issues/942))

This change normalizes the default set of fields to use for all models within the REST API. The `id`, `url`, `display_url` (when available) and `display` fields are now always exposed in both regular and nested serializers.

It also introduces the `fields` and `exclude` query parameters that take comma separated lists of fields that must be returned or excluded by API serializers. This can be useful when users are interested in having just a limited set of fields when querying the API.

Finally, the `config_context` for objects having it is now exposed. It will provide a full rendered config context which should be more complete than the `local_context_data` field.

#### Add mechanism to hide available peers ([#392](https://github.com/peering-manager/peering-manager/issues/392))

A new `HiddenPeer` model has been introduced. It is used to track potential peers to hide and not show in available peer list. This can be used for example when a potential peer refused to peer for various reasons, it can be therefore hidden so it won't be shown for a given IXP anymore.

A peer matching a hidden peer record will be hidden indefinitely, unless the record is deleted or the record `until` timestamp is in the past. Expired records won't be deleted by the housekeeping task, so they will remain until a user deletes them.

#### Store AS lists ([#858](https://github.com/peering-manager/peering-manager/issues/858))

This change adds a new `as_list` field to autonomous system objects. This field is used to store a list of ASN that can be part of the AS paths of routes advertised by an AS. This is useful to design robust policies.

This change also deprecates the `grab_prefixes` command in favour of the `get_irr_data` one. While they are fairly similar, the latter will cache AS lists in addition to prefixes.

Finally, a new `as_list` Jinja2 filter is introduced to be able to use AS lists inside templates. Using this filter will populate the AS list for the autonomous system if it has not been cached previously.

#### Allow per AS overrides of IRR operations ([#128](https://github.com/peering-manager/peering-manager/issues/128))

This change implements several ways to control how prefix lists and AS lists are retrieved by giving per autonomous system granular customization.

* Add a boolean field to control whether prefixes should be retrieved
* Add a boolean field to control whether AS list should be retrieved
* Add a char field to override IRR sources to use instead of the generally configured ones
* Add a char field to override bgpq3/bgpq4 args to get IPv6 prefixes instead of the generally configured ones
* Add a char field to override bgpq3/bgpq4 args to get IPv4 prefixes instead of the generally configured ones

### Enhancements

* [#941](https://github.com/peering-manager/peering-manager/issues/941) Validate IP pair for direct sessions (addresses must be different, in the same network and not network or broadcast addresses)
* [#720](https://github.com/peering-manager/peering-manager/issues/720) Add filters to allow filtering IXP sessions without corresponding PeeringDB records or in an abandoned state
* [#943](https://github.com/peering-manager/peering-manager/issues/943) Add API endpoint `/api/extras/prefix-list/` to retrieve the prefix lists given a list of AS or AS-SETs (possible parameters can be found in the documentation)
* Add warning when using IX-API version 1, IX-API version 1 is now deprecated and will be phased out by the IXPs using it on 2026-07-01
* Add "Is Abandoned" column in IXP session table
* Add session count column to IXP table
* Add `LOGIN_FORM_HIDDEN` setting to hide username/password form login and display only SSO based authentication methods
* Add REST API request counts metrics in Prometheus exporter
* Add `routing_policies` Jinja2 filter for router

### Bug Fixes

* Fix small always present horizontal scrolling
* Fix "Local AS" not being set by default in router and send e-mail to network forms

### Code Housekeeping / Code Quality

* Upgrade to Django 5.2
* Add official support for Python 3.13 and Python 3.14

### Documentation

* Add a "Getting started" page that explain the concepts found in Peering Manager
* Add documentation for the new `HiddenPeer` model
