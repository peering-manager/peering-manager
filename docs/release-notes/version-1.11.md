## Version 1.11.0 | MARK I (Features release) | 2026-09-02

The 1.11.x releases require Python 3.12 or later as well as PostgreSQL 15 or later.

### Breaking Changes

* Peering Manager now runs on Django 6.1, which raises the minimum Python version to 3.12 and the minimum PostgreSQL version to 15
* The `RoutingPolicy` model has been moved from the `peering` app to `bgp`. Accordingly, its REST API endpoint has been moved from `/api/peering/routing-policies/` to `/api/bgp/routing-policies/`
* The IX-API secret is no longer readable. The `api_secret` field of `/api/extras/ix-api/` accepts a value but never returns one, and the form leaves it empty on edit, where an empty value keeps the recorded secret
* `/api/extras/ix-api/accounts/` now answers to `POST` instead of `GET`, and requires a user allowed to add or change an IX-API

### New Features

#### Peering portal API

A dedicated API surface is now exposed at `/api/peering/portal/`, designed to be consumed by an external "peering portal": a public-facing website that lets other networks request BGP peering with the AS operating Peering Manager.

The portal API covers portal-specific operations only: looking up a requesting network, discovering common peering locations, submitting a peering request and tracking the status of past requests. Operator decisions (accept and reject) and listing of established sessions stay on the standard REST API. The design follows the IETF draft [draft-ramseyer-grow-peering-api](https://datatracker.ietf.org/doc/draft-ramseyer-grow-peering-api/) where compatible.

> [!NOTE]
> This is a first version. Expect rough edges, and expect a later release to change it.

Two new models back this feature. A peering request tracks an incoming request from a network for an affiliated AS, identified by a public tracking ID that can be shared with the requester so they can poll status or cancel without authentication. A requested session tracks a single session inside a request and can be linked to the direct or IXP session that results from accepting it. Accepting a request creates the sessions, with validation to avoid duplicating sessions that already exist, while reject and cancel flows are available as well.

The documentation carries a full integration guide, and [a ready to run portal](https://github.com/peering-manager/peering-portal) is published for operators who would rather not write their own.

#### In-app scheduling for system jobs

Housekeeping and PeeringDB synchronisation can now run on a schedule alongside the `rqworker`, removing the need for cron or systemd timers. Schedules are managed per task from a new **Scheduled Tasks** page under the Admin menu: change the interval, enable or disable, or add one from the catalog, with changes applied without a worker restart.

This is built on a small `JobRunner` framework with `core.ScheduledTask` as the source of truth, which the worker reconciles into the queue. A **Run Now** button recovers a task left stuck after a worker died mid-run and doubles as an on-demand trigger.

This adds a dependency on `django-pgware`.

#### Modernised list views with htmx

List views now use htmx so that paging through objects only re-fetches and reloads the table instead of triggering a full page load. Transitions between pages are smoother and lighter.

#### RFC 9234 BGP roles

Direct and IXP sessions can now carry an optional BGP role as defined by [RFC 9234](https://www.rfc-editor.org/rfc/rfc9234.txt). The role sits next to the existing relationship, which stays a free form label, and is available across the forms, tables, filters, API and detail views like any other session attribute.

The relationship was never meant to describe the protocol level role and only ever applied to direct sessions, so it could not express route server or route server client setups. A dedicated role keeps the commercial relationship and the protocol role independent and covers exchange sessions too. A session established with a route server is constrained to the matching role so the pairing stays consistent with the standard. Sessions also expose the capability code and the expected remote role so configuration templates can build the role and leak prevention configuration without repeating the mapping.

#### Normalised IRR prefix storage

The prefixes resolved from an autonomous system's IRR AS-SET are no longer stored as a JSON blob on the autonomous system. They are now kept as individual prefix list entry rows shared between autonomous systems through a link table, so a prefix that appears in several AS-SETs is stored only once. This removes the multi-megabyte JSON columns (a single route server AS-SET could reach a megabyte), lets the database index and filter prefixes directly, and makes the **Prefixes** tab search, filter by address family and paginate server-side instead of loading the whole list into memory.

A new `prefixes_updated` timestamp records when an AS' prefixes were last fetched and is exposed on the API. The `as.prefixes` template variable, the `prefix_list` Jinja2 filter, the opt-in `prefixes` API field and the `as-set-prefixes` API endpoint all keep returning the same `{"ipv6": [...], "ipv4": [...]}` structure, with three behavioural changes worth noting: entries are ordered deterministically (by address family then network, no longer in raw bgpq output order), duplicate entries coming from several AS-SET sources are collapsed, and the `exact` flag is always present. Entries that stop being referenced by any autonomous system are reclaimed by the housekeeping job and at the end of a full `get_irr_data` run.

> [!IMPORTANT]
> The upgrade migrates all cached IRR data into the new tables. On large installations this rewrite can take several minutes; it is idempotent and can be resumed by re-running `migrate` if interrupted.

### Enhancements

* Replace Select2 with Tom Select, which is actively maintained and ships Bootstrap 5 styles
* Redesign the table column configuration modal with a two-pane transfer list to drag columns between available and displayed, reorder them and filter with a search box
* Add category and private fields to communities
* [#907](https://github.com/peering-manager/peering-manager/issues/907) Add an ingress+egress community type so a community can be applied in both directions, along with `is_ingress`/`is_egress` properties and a `direction` argument on the `communities` Jinja2 filter
* [#907](https://github.com/peering-manager/peering-manager/issues/907) Pre-select the affiliated AS the user is currently acting on behalf of as the local AS when creating sessions, IXPs, routers, peering requests or sending an e-mail to a network
* [#907](https://github.com/peering-manager/peering-manager/issues/907) Let operators set default table columns for all users from a table's configuration modal, manageable under Customisation > Table Configurations. The columns a user picks always take precedence
* [#882](https://github.com/peering-manager/peering-manager/issues/882) Push the configuration diff to the data source
* [#818](https://github.com/peering-manager/peering-manager/issues/818) Add a shortcut on the router list to open a router's configuration directly
* [#818](https://github.com/peering-manager/peering-manager/issues/818) Review and commit the configuration of several selected routers at once from a new bulk configuration page
* [#818](https://github.com/peering-manager/peering-manager/issues/818) Add a copy button for the configuration diff and make automatic configuration generation optional on the configuration tab
* Add `encrypt_password` Jinja2 filter
* Add `import_*` and `from_*` template tags
* Add `PEERING_REQUEST_SESSION_STATUS` setting to control the status applied to sessions created when accepting a peering request
* Add `PEERING_REQUEST_BLOCKS_SESSION_CREATION` setting to block creating a session that is already part of a pending peering request
* [#969](https://github.com/peering-manager/peering-manager/issues/969) No longer include the cached IRR data (`prefixes` and `as_list`) in autonomous system API responses by default, as they can weigh several megabytes. Ask for them with the `fields` query parameter
* Add `IXAPI_TIMEOUT` and `CACHE_IXAPI_TIMEOUT` settings, so an unresponsive exchange no longer holds a worker
* Report the failure instead of a server error when an IX-API exchange cannot be reached, so its pages stay readable
* Drop the cached IX-API data when the URL, key or secret of an endpoint changes, and after Peering Manager writes a MAC address to that endpoint
* Expose the PeeringDB port location of the available peers of an IXP, with filters by facility and by remote peering
* Offer the table configuration modal on the peer lists, which never had it
* The interface should now work on a small screen

### Bug Fixes

* Fix the `exclude` query parameter, which previously matched on the raw query string and leaked exclusions across requests, and document it in OpenAPI
* [#818](https://github.com/peering-manager/peering-manager/issues/818) Show the "Deploy On Selected" button on the router list, previously hidden by an incorrect permission check
* [#972](https://github.com/peering-manager/peering-manager/issues/972) Keep the prefixes already stored for an autonomous system when an IRR lookup fails, which used to store an empty or partial list
* Fix setting a MAC address in IX-API, which never worked because the request was malformed
* Match an IX-API network service config to a connection with an IPv6 address, which never matched because the address was compared against the IPv4 column
* Fix the IX-API tab of an IXP when a connection is single stack or when a network service does not carry a subnet, which raised a server error and hid the tab content
* Do not send the IX-API key, secret and tokens in webhook bodies. The change log already hid them; the webhook payload and its before/after snapshots did not
* Give each affiliated AS its own IXP when importing from PeeringDB. A second affiliated AS reused the IXP of the first one, which then offered the IP addresses of the other AS as peering candidates. Existing mixed IXPs need the extra connections to be moved by hand
* Accept any 2XX answer from a webhook receiver. Only `200 OK` counted, so a receiver that answers `204 No Content`, such as Discord, looked like a failure
* Render a boolean table column with no value as a muted dash instead of a red cross
* Hide the password tab and refuse the password form for a user that single sign-on or LDAP authenticates, who has no local password to change
* Hash the password that `/api/users/users/` sets on an existing user. Only the create path hashed it, so an update wrote the password to the database as it is and locked the account out

### Code Housekeeping / Code Quality

* Auto-annotate model multiple choice filters for the OpenAPI schema
* Expand bulk edit forms with missing scalar fields
* Remove the leftover poetry resources. `uv` is the only supported tool, `uv.lock` the only lockfile, and the pre-commit and Read the Docs configurations now call `uv`
* Move the e-mail server settings to Django's `MAILERS` setting, which replaces the `EMAIL_*` settings Django deprecated. The `EMAIL` configuration parameter is unchanged
* Cache IX-API answers as plain data instead of `pyixapi` records, which copied the key, the secret and the tokens to Redis with every entry
* Send single sign-on requests as `POST` forms, which `social-auth-app-django` 6.0 requires on the login start view

### Documentation

* Add a peering portal integration guide, and point it at a ready to run portal
* Add a peering request e-mail template example
* Add a Discord notification example to the webhook documentation
* Point in-app documentation links at `docs.peering-manager.net` instead of the old Read the Docs URLs
