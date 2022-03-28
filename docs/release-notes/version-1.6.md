## Version 1.6.1 | MARK I (Bug fixes release) | 2022-03-29

### Enhancements

* Prevent browser password manager prepopulating BGP/NAPALM passwords
* Global rework of generic views
* Log error reaching PeeringDB (i.e. auth issue)
* Add e-mail settings example to documentation
* Display an icon for objects linked to PeeringDB
* [#568](https://github.com/peering-manager/peering-manager/issues/568) Fix multihop session validation and API validation for direct sessions

### Bug Fixes

* Do not always create placeholder contact role on database migration
* Fix upgrade instructions link
* Fix config compare for router in maintenance
* Do not import connections without IP addresses from PeeringDB
* Fix PeeringDB linking after a cache flush
* Fix IX-API lookup for remote v2 endpoints
* [#570](https://github.com/peering-manager/peering-manager/issues/570) Change PeeringDB URL to avoid HTTP 301 redirect

## Version 1.6.0 | MARK I (Features release) | 2022-02-28

The 1.6.x releases will be the last ones to support Python 3.6 and Python 3.7 as well as PostgreSQL 9.6. It is recommended for users to pro-actively upgrade their environments to use at least Python 3.8 and PostgreSQL 10 for safer upgrades.

### New Features

#### API Breaking Changes

1. Endpoint `/api/peering/emails` moved to `/api/messaging/emails`
2. Endpoint `/api/peering/configurations` moved to `/api/devices/configurations/`
3. New endpoint `/api/messaging/contact-assignments/`
4. New endpoint `/api/messaging/contact-roles/`
5. New endpoint `/api/messaging/contacts/`
6. Removed `bgp_session_states_update` and `check_bgp_session_states` from BGP group and Internet exchange objects
7. Add `poll_bgp_sessions_state` and `poll_bgp_sessions_last_updated` to router objects
8. Replace `/api/peering/bgp-groups/{id}/poll-sessions` by `/api/peering/bgp-groups/{id}/poll-bgp-sessions`
9. Replace `/api/peering/internet-exchanges/{id}/poll-sessions` by `/api/peering/internet-exchanges/{id}/poll-bgp-sessions`
10. New endpoint `/api/peering/routers/{id}/poll-bgp-sessions`
11. New endpoint `/api/peering/autonomous-systems/{id}/poll-bgp-sessions`
12. Use CIDR notation for the `ip_address` field of direct peering sessions

#### Global Search

A new search bar is available on the homepage to search for objects inside the whole database. Searchable objects include connections, autonomous systems, BGP groups, communities, direct peering sessions, configurations, e-mails, Internet exchange points, Internet exchange peering sessions, routers and routing policies.

#### Contacts

Contacts and contact roles have been added to record point of contacts for autonomous systems. Contacts can be used to track people or teams and details to reach out to them (by e-mail or by phone). A contact for an autonomous system is assigned and given a role using and assignment object, allowing a contact to be re-used several times with different roles on different autonomous systems.

E-mail templates have also moved into the same "Messaging" menu that contacts belongs to. During the migration process tags on e-mail templates will not be preserved as objects are going to be recreated and old ones will be deleted.

#### Devices Menu

Configurations templates, platforms and routers have been moved into a dedicated menu called "Devices". This change also reflects cleanup that has been performed and that will be performed in a near future in the code base. During the migration process tags on configuration templates will not be preserved as objects are going to be recreated and old ones will be deleted.

#### Direct BGP Sessions Prefix Length ([#358](https://github.com/peering-manager/peering-manager/issues/358))

Enable prefix aware local and remote IPs for direct peering sessions. Sessions with local IP set must have a remote IP that belong in the same subnet as the local. This change may break templates as it will include the prefix length when accessing the `ip_address` field of a session. If you want to use the value without the prefix length use the `ip` filter provided as part of the templating engine like `{{ session | ip }}`.

A new command `fix_direct_sessions_net` can be used to guess direct sessions subnets. Sessions without local IP will be ignored as well as sessions with local and remote IP belonging to the same subnet.

#### BGP Sessions Polling Refactoring ([#201](https://github.com/peering-manager/peering-manager/issues/201), [#334](https://github.com/peering-manager/peering-manager/issues/334))

Polling BGP sessions used to be done on a per-group or per-IXP basis. This feature is now provided per-router to optimise the polling process. The process will always be done using background tasks. You can still ask for group or IXP sessions to be polled from the user interface. It will automatically schedule as many background tasks as necessary for each router belonging to the group or connected to the IXP. The poll sessions button has been added in autonomous system session views.

The `poll_peering_sessions` command has been removed and its feature has been moved to a new `poll_bgp_sessions` command.

### Enhancements

* Make webhook thread safe, also improve many-to-many relationships and fire webhook only once
* [#523](https://github.com/peering-manager/peering-manager/issues/523) Allow config context format to be displayed as JSON or YAML
* Add link to Swagger UI in the footer
* Allow search by ASN in the generic search field
* Gracefully fail when loading IX-API details for an IXP if the remote IX-API appears to be unreachable
* [#537](https://github.com/peering-manager/peering-manager/issues/537) Add support for IX-API v2 accounts endpoint
* Set affiliated autonomous system by default when adding a direct session
* [#440](https://github.com/peering-manager/peering-manager/issues/440) Add unique constraint to avoid duplicate IXP session on a same connection
* Add optional parameter `family` to both `iter_export_policies` and `iter_import_policies`
* [#440](https://github.com/peering-manager/peering-manager/issues/440) Forbid to add an IXP session with the same IP address on the same connection
* [#314](https://github.com/peering-manager/peering-manager/issues/314) Add dedicated tab to AS to show known PeeringDB info, add traffic and policy related data to available peers list
* Limit possible connections to the current IXP when adding a new IXP session
* [#470](https://github.com/peering-manager/peering-manager/issues/470) Add `--tasks` flag to `poll_bgp_sessions` and `configure_routers` commands

### Bug Fixes

* [#521](https://github.com/peering-manager/peering-manager/issues/521) Discard configuration on device if installation fails
* [#522](https://github.com/peering-manager/peering-manager/issues/522) Invalidate PeeringDB objects when flushing the cache
* [#527](https://github.com/peering-manager/peering-manager/issues/527) Fix identities loading when editing an IX-API object
* [#531](https://github.com/peering-manager/peering-manager/issues/531) Fail IX-API object validation if authentication fails
* Fix connection count in IXP list
* Do not display buttons in table when reviewing a list to delete or edit multiple objects
* Fix `<pre>` blocks to display errors without extra spaces
