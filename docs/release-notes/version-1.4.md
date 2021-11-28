# Peering Manager v1.4 Release Notes

## Version 1.4.6 | MARK I (Bug fixes release) | 2021-10-28

Note: as of this release, WSGI servers such as gunicorn or uwsgi are no longer listed as dependencies. You may continue to list them as local dependencies in your setup by creating a `local_requirements.txt` next to `requirements.txt`. This is also true for LDAP and RADIUS authentication packages.

### Enhancements

* Allow extra packages to install to be listed with `local_requirements.txt`
* Return `QuerySet` for `communities` Jinja2 filter
* Make commands output to stdout
* Allow use of `filter` Jinja2 filter on item list with attributes
* Set proper prefix length on connection import
* Use cached data to preload AS details
* Add `render_configuration` command to help users testing templates from the CLI
* Add Jinja2 trim and lstrip to templates (configuration and e-mail) for better whitespaces control
* [#492](https://github.com/peering-manager/peering-manager/issues/492) Add RS filter field to available peers

### Bug Fixes

* Fix PeeringDB facility voltage field
* Fix `ipv4` and `ipv6` Jinja2 filters for CIDR addresses
* Fix Python version requirement check
* Fix polling of IXP sessions with the same IPs on different IXP connections
* [#497](https://github.com/peering-manager/peering-manager/issues/497) Fix NetBox > 3.0 integration
* [#500](https://github.com/peering-manager/peering-manager/issues/500) Fix sessions import for AS page

## Version 1.4.5 | MARK I (Bug fixes release) | 2021-10-06

### Enhancements

* [#310](https://github.com/peering-manager/peering-manager/issues/310) Improve setup documentation (by @Paktosan)
* [#427](https://github.com/peering-manager/peering-manager/issues/427) Improve change logging with pre-change data
* [#473](https://github.com/peering-manager/peering-manager/issues/473) Add `has_tag` / `has_not_tag` Jinja filters
* [#476](https://github.com/peering-manager/peering-manager/issues/476) Allow mask length in connection IPs
* [#471](https://github.com/peering-manager/peering-manager/issues/471) Add cache time for NAPALM neighbor details with `CACHE_BGP_DETAIL_TIMEOUT` setting (by @mngan)
* [#489](https://github.com/peering-manager/peering-manager/issues/489) Add `communities` and `merge_communities` Jinja filters
* Add configuration context field to the `Connection`s
* Add new `connections` Jinja filter that will return an iterator to loop over the connections of a router or an IXP
* Add templating tutorial (by @Paktosan)
* Sync PeeringDB's models with 2.9.0.1
* Expose HTTPS settings with `USE_X_FORWARDED_HOST` and `SECURE_PROXY_SSL_HEADER`, defaults to try using HTTPS if possible

### Bug Fixes

* Fix webhook enqueuing
* Prohib Django's LogEntry to fire a webhook
* Fix error log on missing NAPALM driver
* Fix broken HTML tag in community detail view
* Fix `local_ips` IP version filtering
* [#488](https://github.com/peering-manager/peering-manager/issues/488) Use IXP instance when adding sessions, default to the first matching IXP if IXP is not explicitly used

## Version 1.4.4 | MARK I (Bug fixes release) | 2021-07-04

### Enhancements

* Limit RAM usage by deferring prefixes loading for autonomous systems (except in the API)
* Delete connections to an IXP when said IXP is deleted, thus deleting peering sessions too
* [#371](https://github.com/peering-manager/peering-manager/issues/371) Add CC field to e-mails based on CC_CONTACTS setting
* [#457](https://github.com/peering-manager/peering-manager/issues/457) Add communities objects to autonomous systems

### Bug Fixes

* Fix a bunch of form filter labels
* Fix initial data when creating a direct peering session for a group
* Set default state of router to enabled
* Remove icon HTML code from page title
* Make sure that local and remote IP addresses are from the same IP families when creating a direct peering session
* Validate that routing policies address family matches the session address family when assigning them

## Version 1.4.3 | MARK I (Bug fixes release) | 2021-06-21

### Enhancements

* [#447](https://github.com/peering-manager/peering-manager/issues/447) Bring back `raw` configuration button

### Bug Fixes

* [#448](https://github.com/peering-manager/peering-manager/issues/448) Filter out policies that don't match the session IP family
* [#455](https://github.com/peering-manager/peering-manager/issues/455) Fix IXP session count in router list
* [#456](https://github.com/peering-manager/peering-manager/issues/456) Don't fail when polling down BGP sessions


## Version 1.4.2 | MARK I (Bug fixes release) | 2021-06-15

### Enhancements

* [#400](https://github.com/peering-manager/peering-manager/issues/400) Add command `import_all_ix_sessions` to import all IXP sessions from routers
* [#319](https://github.com/peering-manager/peering-manager/issues/319) Add IXP session from AS view
* Expose general peering policy from PeeringDB in AS list and AS details views

### Bug Fixes

* Fix Redis databases documentation
* Fix IXP sessions polling using `poll_peering_sessions` command
* Fix connection state update
* Fix "Add selected" button (broken in 1.4.1)

## Version 1.4.1 | MARK I (Bug fixes release) | 2021-06-11

### Enhancements

* Flush PeeringDB cache data more aggressively when using `--flush` flag
* Set PeeringDB synchronisation job timeout to one hour
* Automatically link IXPs and connections to PeeringDB after a successful synchronisation

### Bug Fixes

* Redirect user with an error message if "Add selected" is clicked without any selection
* Fix HTML code injection on IXP import

## Version 1.4.0 | MARK I (Features release) | 2021-06-09

This release is the first one with @jamesditrapani as one of the maintainers of Peering Manager.

Big thanks [DE-CIX](http://www.de-cix.net) and [Virtual Technologies and Solutions](https://www.vts.bf/) for sponsoring this release.

### New Features

#### `OR` Logic For API Filters ([#293](https://github.com/peering-manager/peering-manager/issues/293))

Several values can be used with a filter to look for more than one objects of the same type. Queries such as `?asn=64500&asn=64501` will return 2 objects matching either one or the other condition. To perform such lookup we generate new filter fields accepting multiple values while still maintaining the original field validation method to keep filtering single values.

#### State Field To Routers ([#291](https://github.com/peering-manager/peering-manager/issues/291))

A router can now be set in different states to avoid deploying configurations on it. While being enabled a router will continue to receive config updates as usual. In maintenance, configurations can also be installed but a confirmation will be asked. When disabled, no configurations will be sent to the router.

#### Platforms ([#347](https://github.com/peering-manager/peering-manager/issues/347))

A platform is a model used to define network operating systems. A router can have a platform set, allowing Peering Manager to interact with it, as long as a NAPALM driver is available. New platforms can be created by users, which can use community-driven NAPALM drivers. Users are not limited to default platforms anymore. Existing routers and platforms will be migrated on upgrade.

#### Background Tasks And Results

Code that take a long time to run as always been problematic inside Peering Manager. Moreover a lot of this kind of code is required to provide new features and better control over current operations.

A new job results view is provided to ensure that a task is queued and to also hold info about the task itself, such as its status, logs, ID in the Redis queue, … Several jobs have been moved as background tasks to improve performances and workflows.

* Router configuration rendering
* Installation of configurations on devices
* BGP sessions import from router
* Poll of session states
* PeeringDB cache filling

Be aware that API endpoints corresponding to these tasks now returns a serialized job result to help your keep track of the tasks asynchronously.

#### Connections ([#246](https://github.com/peering-manager/peering-manager/issues/246))

A Connection is an object that connect a local autonomous system to an Internet exchange point. It holds details about router, IP addresses and connectivity to the IXP itself. As a consequence an Internet exchange object no longer holds these properties. It is now used as a way to group connections thus allowing multiple connections to the same IXP without having to duplicate objects.

During the upgrade, connections will be created and affected to IXPs automatically. To avoid messing with user's data, all IXPs will be kept, one (and only one) connection will be created for each IXP. Users can then decide to link a connection to another IXP object, eventually leading to the removal of the duplicate IXPs.

#### Jinja2 Filters([#356](https://github.com/peering-manager/peering-manager/issues/356))

New Jinja2 filters are available to help writing templates (configurations and e-mails). These filters come with a lot of refactoring templates and their associated variables. Be sure to review the documentation before upgrading in order adjust existing templates.

### Enhancements

* Remove affiliated autonomous system warning for non-authenticated users
* Validate TTL minimum and maximum values
* [#281](https://github.com/peering-manager/peering-manager/issues/281) Use RADB as default IRR for `bgpq3` lookup
* Use `q` filter field for characters/strings based filtering (affecting API)
* [#233](https://github.com/peering-manager/peering-manager/issues/233) Add help text to slug fields warning users about editing them
* Use ISO8601 format for date and time by default
* Add `LOGIN_BANNER` setting to show a banner on the login page
* [#64](https://github.com/peering-manager/peering-manager/issues/64) Add a provisionning view listing all potential sessions on all IXPs
* Use database 64-bit IDs
* [#377](https://github.com/peering-manager/peering-manager/issues/377) Allow filtering on AS Name and Peering Policy
* [#367](https://github.com/peering-manager/peering-manager/issues/367) Add unique service reference fields to BGP sessions (empty by default)
* [#407](https://github.com/peering-manager/peering-manager/issues/407) Add `PEERINGDB_API_KEY` setting to authenticate with PeeringDB, username and password authentication will be dropped in version 2.0.0.
* [#287](https://github.com/peering-manager/peering-manager/issues/287) Add configuration context field (JSON format) to routers and routing policies (by @ggidofalvy-tc)
* [#426](https://github.com/peering-manager/peering-manager/issues/426) Use IDs for URL routing everywhere dropping slugs and ASN, you may need to change links to Peering Manager in your other tools
* Remove default logging configuration, users must now setup the logging configuration following Django and Python documentation

### Bug Fixes

* [#388](https://github.com/peering-manager/peering-manager/issues/388) Remove raw configuration output (not compatible with asynchronous job)
* Fix prefix fetching to log a warning on exceptions, to avoid crash and attempt to fill in all the ASNs, to ignore errors with `--ignore-errors` flag (by @mngan)
* [#372](https://github.com/peering-manager/peering-manager/issues/372) Add `--limit` flag to `configure_routers` command
* [#195](https://github.com/peering-manager/peering-manager/issues/195) Add missing documentation around PeeringDB
* Remove legacy clear BGP session API call as it was not used by most users
* Use correct documentation link, with versioning (by @Paktosan)
