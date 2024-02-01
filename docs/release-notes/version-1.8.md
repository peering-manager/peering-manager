## Version 1.8.3 | MARK I (Bug fixes release) | 2024-02-01

### Bug Fixes

* Fix use of multiple `include_*` directive in templates (by @rwielk)
* Fix cosmetic issue with PeeringDB synchronisation button in AS view
* Fix filtering based on `created_by_request` and `updated_by_request` fields
* Fix XSS security issue when rendering link to objects
* Fix redirection issue where form could redirect to absolute URLs
* Use sandboxed Jinja2 environment to render templates to avoid obvious security issues

### Enhancements

* [#687](https://github.com/peering-manager/peering-manager/issues/687) Add filtering capabilities for PeeringDB objects in the API
* [#742](https://github.com/peering-manager/peering-manager/issues/742) Add view to be able to send an e-mail to a PeeringDB network which has not been added as an AS (see example in documentation)
* [#766](https://github.com/peering-manager/peering-manager/issues/766) Bring back RADB, ALTDB, NTTCOM, LEVEL3, TC and RIPE-NONAUTH as default sources for prefix lookup
* [#786](https://github.com/peering-manager/peering-manager/issues/786) Support PeeringDB validated update feature for affiliated autonomous systems
* Consolidate middlewares into a single one
* Allow filtering autonomous systems by ASN and/or name in the API
* Move `/provisioning/available-ix-peers/` to `/peeringdb/available-ixp-peers/`
* Add `PEERINGMANAGER_CONFIGURATION` environment variable to change configuration module to load
* Record accepted prefix count in addition to received prefix count when polling BGP sessions
* Add `shared_facilities` Jinja2 filter to get a list of facilities in which both networks are, according to PeeringDB records
* Autonomous system e-mail view has been tweaked to make it consistent with the new Provisioning > Send E-mail To Network view
* Refactoring of the documentation which is also available at https://docs.peering-manager.net

## Version 1.8.2 | MARK I (Bug fixes release) | 2023-09-29

### Bug Fixes

* [#768](https://github.com/peering-manager/peering-manager/issues/768) Fix broken config contact assignment view
* [#775](https://github.com/peering-manager/peering-manager/issues/775) Fix NetBox display in router add/edit form
* Fix crash when showing routing policies column in tables
* Fix filtering by tags when clicking a tag (by @rwielk)
* Fix platform main URL that redirects to routers using the given platform (by @rwielk)
* Restore UNIX socket support for redis (by @yu-re-ka)

## Version 1.8.1 | MARK I (Bug fixes release) | 2023-09-18

### Bug Fixes

* [#760](https://github.com/peering-manager/peering-manager/issues/760) Fix bug removing table columns when trying to order a column
* [#763](https://github.com/peering-manager/peering-manager/issues/763) Fix regression preventing from using bulk edit views and forms
* Fix upgrade script trying to invalidate cacheops cache which is not used anymore

### Enhancements

* [#761](https://github.com/peering-manager/peering-manager/issues/761) Allow filtering BGP sessions by BGP state
* Add `passive` field to BGP sessions (IXP and direct) to denote a session that will wait for open messages
* Add `multihop_ttl` column to BGP sessions (IXP and direct) tables

## Version 1.8.0 | MARK I (Features release) | 2023-09-15

The 1.8.x releases require Python 3.8 or later as well as PostgreSQL 12 or later.

### New Features

#### API Breaking Changes

* The `JobResult` model has been moved from the extras app to core and renamed to `Job`. Accordingly, its REST API endpoint has been moved from `/api/extras/job-results/` to `/api/core/jobs/`
* The `obj_type` field on the `Job` model (previously `JobResult`) has been renamed to `object_type` for consistency
* The `JOBRESULT_RETENTION` configuration parameter has been renamed to `JOB_RETENTION`
* The URLs for the REST API schema documentation have changed:
  * `/api/docs/` is now `/api/schema/swagger-ui/`
  * `/api/redoc/` is now `/api/schema/redoc/`
* The `Tag` model has been moved from the utils app to extras. Accordingly, its REST API endpoint has been moved from `/api/utils/tags/` to `/api/extras/tags/`
* The `ObjectChange` model has been moved from the utils app to extras. Accordingly, its REST API endpoint has been moved from `/api/utils/object-changes/` to `/api/extras/object-changes/`
* The `CACHE_TIMEOUT` configuration parameter has been removed

#### API Code General Housekeeping

A lot of efforts has been put in making the global code base more maintainable and future proof. This shouldn't have impact on using Peering Manager in general. However it brings some changes to users as well by improving API schema.

Also changing the selected affiliated AS via API as seen its dedicated endpoint removed. It is still possible to change it but users must now use the user preferences endpoint at `/api/users/userpref/`.

This global code refactoring is also the reason of the above mentioned API breaking changes and the below mentioned models normalisation.

#### Models Normalisation

Models have been normalised using common classes and now inherit automatically some fields. This means that some fields (`name`, `slug`, `description`) have been added to some models.

All `name` fields have been limited to 100 characters as well as the `slug` fields. If values in these fields exceed the 100 characters limit, you'll need to adjust them prior to the upgrade.

#### Move IX-API Code To `pyixapi`

Fields has been added to store IX-API tokens and their respective expiration times. The use of `pyixapi` allows cleaner code and better maintainability. Data retrieval has been improved and is now faster by fetching all data instead of doing multiple calls to IX-API instances with filtering. Data correlation is done in memory but it should not explode in RAM as data amount is relatively small.

#### IP Prefix Lookup Default Settings ([#735](https://github.com/peering-manager/peering-manager/issues/745))

To lookup prefixes, the default settings used to include a long list of IRR sources, some of them being less relevant as of today (year 2023). This list has been reduce to include only authoritative sources as the default. This means that it now includes:

* RIPE
* ARIN
* APNIC
* AFRINIC
* LACNIC
* RPKI, a pseudo source used by IRRd v4 servers

The default host for prefix lookup has been changed to use NTT's which is located at `rr.ntt.net`.

These changes are made in an attempt to follow Internet best pratices in term of IRR trust by deprecating non-authoritative sources.

#### Webhook Framework Improvements ([#719](https://github.com/peering-manager/peering-manager/issues/719))

The webhook framework has been extended to allow more flexibility and less triggers.

Webhooks can now be created as regular objects, without the use of the admin panel. They can be found in the "Other" menu of the sidebar and in the `/api/extras/webhooks/` API endpoint.

Also webhooks are now attached to content types which mean they can be triggered only for selected object types. Additional headers can be added, the body of the webhook can be changed using templating and Jinja2. Conditions can be defined to fire a webhook only if some terms are met.

Reviewing the webhook model documentation is highly encouraged to get to know more about it.

#### Status For Sessions, Group And Devices ([#735](https://github.com/peering-manager/peering-manager/issues/735))

It has been raised several times that there were not enough statuses to fit users workflows. Several statuses have been added to address this issue.

Pre and post maintenance statuses for BGP groups, IXPs and devices have been included to better reflect maintenance work and allow according workflow.

BGP sessions have 6 more possible statuses to reflect the life cycle of a session from
requested to decommissioned. Possible statuses are now: requested, provisioning, enabled, pre-maintenance, maintenance, post-maintenance, disabled, decommissioning, and decommissioned.

### Enhancements

* [#740](https://github.com/peering-manager/peering-manager/issues/740) Upgrade to Django 4.2
* [#741](https://github.com/peering-manager/peering-manager/issues/741) Replace django-cacheops with Django builtin cache feature using Redis
* [#737](https://github.com/peering-manager/peering-manager/issues/737) Separate import and export routing policies in object views
* [#678](https://github.com/peering-manager/peering-manager/issues/678) Add PeeringDB's carrier and campus objects to local cache
* [#682](https://github.com/peering-manager/peering-manager/issues/682) Add `contact` Jinja2 filter
* Show tagged items in a tag view
* Allow communities to be linked to other objects (direct sessions, IXP sessions, routing policies)
* Add Jobs tab to router view
* Add `exists_in_peeringdb` IXP session property and display as table column
* Display PeeringDB last synchronisation time in PeeringDB view
* Use pyixapi 0.2 and allow changing MAC address for a connection via IX-API

### Bug Fixes

* [#683](https://github.com/peering-manager/peering-manager/issues/683) When running a job on a router, if it is unusable, log a warning but do not mark the job as failed
* [#684](https://github.com/peering-manager/peering-manager/issues/684) Do not fail session polling with 0 sessions
* [#686](https://github.com/peering-manager/peering-manager/issues/686) Do not commit empty configuration
* [#687](https://github.com/peering-manager/peering-manager/issues/697) Disable PeeringDB features for private ASNs
* [#709](https://github.com/peering-manager/peering-manager/issues/709) Fix config context API serialization
* [#723](https://github.com/peering-manager/peering-manager/issues/723) Use NAPALM version 4.1.0 (by @forkwhilefork)
* [#732](https://github.com/peering-manager/peering-manager/issues/732) Fix contact assigment edit view permission
* Rename unique filter to unique_items to avoid conflict with Jinja2 base `unique`
* Do not show PeeringDB import if no context AS
* Fix NetworkIXLan's cidr, this function could fail in finding a single valid CIDR and broke code relying on it

### Documentation

* Explain how to run multiple rqworkers (by @Paktosan)
* Fix scheduled tasks (by @netravnen)
* Include information to have gunicorn listen on IPv6 `::1` (by @netravnen)
