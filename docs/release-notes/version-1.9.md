## Version 1.9.7 | MARK I (Bug fixes release) | 2025-07-31

### Bug Fixes

* [#925](https://github.com/peering-manager/peering-manager/issues/925) Fix button styling when transitioning from an error state
* [#933](https://github.com/peering-manager/peering-manager/issues/933) Fix git data source backend operations when `HTTP_PROXIES` where defined but without actual values
* [#938](https://github.com/peering-manager/peering-manager/issues/938) Fix performance issue when accessing session list views (both direct and IXP)
* Fix IXP available peer list when no connections are configured
* Raise an error when trying to use a directory based data source that does not exist

## Version 1.9.6 | MARK I (Bug fixes release) | 2025-04-11

### Bug Fixes

* Add `BGPQ4_KEEP_SOURCE_IN_SET` setting to opt in for bgpq4 keep IRR source. The setting is set to `False` by default to go back to the previous behaviour. Setting it to `True` affects the AS-SET or ROUTE-SET resolution which can lead to a drop in the number of routes found.

## Version 1.9.5 | MARK I (Bug fixes release) | 2025-04-10

### Bug Fixes

* Remove pin of ncclient, this should solve an issue when using SSH key for NAPALM without a
password
* [#920](https://github.com/peering-manager/peering-manager/issues/920) Fix non-CRUD API actions permissions

### Enhancements

* Keep IRR source in AS-SET for bgpq4, if bgpq3 is used, query will try to limit itself to the given IRR source if available
* Remove uniqueness constraint for service reference
* Support "starts with" filter for AS lookup by ASN
* [#854](https://github.com/peering-manager/peering-manager/issues/854) Allow referencing connections in direct sessions

## Version 1.9.4 | MARK I (Bug fixes release) | 2025-03-09

### Bug Fixes

* [#911](https://github.com/peering-manager/peering-manager/issues/911) Fix email from address config in docs
* [#916](https://github.com/peering-manager/peering-manager/issues/916) Fix export template data file form fields
* [#909](https://github.com/peering-manager/peering-manager/issues/909) Handle empty host/sources for bgpq arguments (by @jford00)
* Set local AS initial value when adding an IXP

### Enhancements

* Add bulk edit to session list views (by @rwielk)
* Prevent data drift for PeeringDB cache by synchronising each type of records based on its last update time
* Use HTTP proxies for IX-API if configured
* Add support for default user preferences by setting the `DEFAULT_USER_PREFERENCES` value in the configuration

## Version 1.9.3 | MARK I (Bug fixes release) | 2025-02-04

### Bug Fixes

* Fix issue preventing many-to-many relations to be recorded in changelog (affected tags and other changes)
* Fix unreadable breadcrumbs in light mode

### Enhancements

* Add communities column to routing policy table
* Add link to documentation in footer and change some icons

## Version 1.9.2 | MARK I (Bug fixes release) | 2025-01-18

### Bug Fixes

* [#901](https://github.com/peering-manager/peering-manager/issues/901) Hide data source sensitive data and allow showing it using a button
* [#903](https://github.com/peering-manager/peering-manager/issues/903) Catch git push silent errors when trying to push to a protected branch
* [#905](https://github.com/peering-manager/peering-manager/issues/905) Fix table configure moveup/down buttons not updating the column list
* Fix spinning icons for some buttons
* Fix NetBox device field wrongly marked as mandatory

## Version 1.9.1 | MARK I (Bug fixes release) | 2025-01-14

### Bug Fixes

* Fix login page HTML for alert closing button
* Fix response when IX-API MAC update fails
* [#888](https://github.com/peering-manager/peering-manager/issues/888) Fix call logging when checking if a router can be used with NAPALM (by @rwielk)
* [#902](https://github.com/peering-manager/peering-manager/issues/902) Fix bulk deploy on routers modal now showing

### Enhancements

* [#900](https://github.com/peering-manager/peering-manager/issues/900) Add `now` Jinja2 function that can be called in templates like `{{ now() }}`

### Documentation

* Minor tweaks in setup instructions to make them a bit more clear regarding PostgreSQL
* Add VyOS template (by @Charlie-Root)

## Version 1.9.0 | MARK I (Features release) | 2024-11-20

The 1.9.x releases require Python 3.10 or later as well as PostgreSQL 13 or later.

### API Breaking Changes

* The `Router` model has been moved from the `peering` app to `devices`. Accordingly, its REST API endpoint has been moved from `/api/peering/routers/` to `/api/devices/routers/`
* The `use_netbox` field of the `Router` model has been deleted as NetBox cannot be used as a NAPALM proxy by default
* The `ObjectChange` model has been moved from the `extras` app to `core`. Accordingly, its REST API endpoint has been moved from `/api/extras/object-changes/` to `/api/core/object-changes/`

### New Features

#### External Data Sources ([#365](https://github.com/peering-manager/peering-manager/issues/365) and [#675](https://github.com/peering-manager/peering-manager/issues/675))

A first version of external data sources is available. It allows users to reference local file system directories or git repositories in order to synchronise files found in those sources and use them as templates.

Device configurations, e-mails, configuration contexts and export templates can be set to use a file found in a data source. This is particularly useful to keep track of templates in, e.g. a git repository without having to copy/paste the content of a file inside Peering Manager.

A mechanism to automatically synchronise file content is also provided which allows automatic update of templates when data sources are synchronised.

Data sources can be synchronised either by clicking on the appropriate button in the user interface or by calling the `datasource` CLI commands like `python manage.py datasource source1 source2` with `source1` and `source2` being names of data sources. A `--all` flag can also be used to synchronise all known data sources without having to mention their names.

In addition to fetching templates from data sources, these same sources can be used a location to push device configurations too. This means that a device configuration can be pushed and stored in a directory or a git repository. This is done separately from pushing the configuration to the device.

#### Remote User Authentication ([#330](https://github.com/peering-manager/peering-manager/issues/330))

To improve authentication for remote users or by using external authentication methods, Peering Manager now integrates with [`python-social-auth`](https://github.com/python-social-auth). This enables Single Sign-On (SSO).

!!! warning
    People using legacy OIDC or SAML2 Peering Manager implementations need to migrate to the new SSO implementation.

To provide user authenticate via a remote backend in addition to local authentication, the `REMOTE_AUTH_BACKEND` configuration parameter must be set to a suitable backend class. The following classes are available by default:

* LDAP: `REMOTE_AUTH_BACKEND = "peering_manager.authentication.LDAPBackend"`
* HTTP Header Authentication: `REMOTE_AUTH_BACKEND = "peering_manager.authentication.RemoteUserBackend"`

To enable SSO, specify the path to the desired authentication backend within the `social_core` Python package. Please see the complete list of [supported authentication backends](https://github.com/python-social-auth/social-core/tree/master/social_core/backends) for the available options, e.g.

```python
REMOTE_AUTH_BACKEND = "social_core.backends.google.GoogleOAuth2"
```

More details are available in the [dedicated documentation page](https://docs.peering-manager.net/administration/authentication/).

#### BFD Model

Add a new model to document BFD (Bidirectional Forwarding Detection) configurations. This fast failure detection protocol can be coupled with BGP in order to trigger a faster re-routing of traffic.

The current model exposes timers and detection multiplier often used by network operating system as parameters for BFD sessions. More detailed explanations are available in [the documentation](https://docs.peering-manager.net/models/net/bfd/).

BFD configurations can be linked to BGP sessions (both IXP and direct ones).

#### BGP Community Value Validation ([#479](https://github.com/peering-manager/peering-manager/issues/479))

Validating BGP community values consist of making sure that they follow a pattern that can properly represent communities according to RFC1997, RFC4360 and RFC8092. Therefore, BGP communities can be represented like:

* `<16-bit int>:<16-bit int>` for RFC1997
* `(origin|target):<32-bit int>:<16-bit int>` or `(origin|target):<16-bit int>:<32-bit int>` for RFC8092
* `<32-bit int>:<32-bit int>:<32-bit int>` for RFC8092

As this behaviour can break the way a user expresses communities, the validation can be turned off by setting `VALIDATE_BGP_COMMUNITY_VALUE = False` in the configuration if needed.


#### Dark and Light Modes ([#380](https://github.com/peering-manager/peering-manager/issues/380))

Stop burning you eyes in the middle of the night when looking at your BGP toolbox during your on-call rotation. Upgrading Bootstrap to version 5.3 allows to take advantage of the dark and light themes provided out of the box by the popular frontend toolkit. This work has been missing for quite a while and provide an updated user experience when using Peering Manager user interface.

There is still some work to be done to refactor the style and views but users should see some improvements already. The top and side bars have been reviewed to provide a style suitable for dark and light modes. Colours, spacing, icons and more have been tweaked here and there.

#### Census Reporting

Peering Manager now makes a call to a remote server to send a census report each time a worker starts (WSGI server or RQ worker). This census report includes anonymous data such as a pseudorandom unique identifier, the version of Peering Manager and the Python version being used.

This reporting can be disabled by setting `CENSUS_REPORTING_ENABLED` to `False` in the configuration file. Census reporting is disabled automatically in debug mode and during unit tests. Keep in mind that this reporting is useful for Peering Manager maintainers to better understand the install base.

Since Peering Manager as always be about being open and fully transparent to users, the code of the reporting server has been published in a [GitHub repository](https://github.com/peering-manager/census-server). The server is available at `https://census.peering-manager.net`, it records census reports in a PostgreSQL database and sends a notification to a Discord channel when a census report is created or updated.

### Enhancements

* Upgrade to Django 5
* Drop official support for Python 3.8 and 3.9
* Add official support for Python 3.12
* [#112](https://github.com/peering-manager/peering-manager/issues/112) Show common facilities according to PeeringDB in an AS PeeringDB view
* Option to select a custom configuration to deploy when using `configure_routers` CLI (by @rinsekloek)
* Add communities column to different tables (by @rinsekloek)
* Update autonomous systems details after PeeringDB synchronisation triggered as a background job
* Expose new login/session/cookie related settings `LOGIN_PERSISTENCE`, `LOGIN_TIMEOUT`, `SESSION_COOKIE_NAME`, `SESSION_COOKIE_SECURE` and `SESSION_FILE_PATH` (see documentation for more details)
* Add table showing common facilities in autonomous system PeeringDB tab
* Do not log a change if an object was saved without changes made to it
* Do not log sensitive fields for IX-API objects in the changelog
* [#856](https://github.com/peering-manager/peering-manager/issues/856) Synchronise BFD support for PeeringDB records
* Support PeeringDB fields to know if a network is connected in the same facility as the IXP
* Expose the description field for autonomous systems
* [#864](https://github.com/peering-manager/peering-manager/issues/864) Add comments to match on when searching for BGP sessions (by @rwielk)
* [#866](https://github.com/peering-manager/peering-manager/issues/866) Allow searching community by value (by @rwielk)
* [#877](https://github.com/peering-manager/peering-manager/issues/877) Allow adding communities to routers (by @rwielk)
* Allow lookup of PeeringDB contacts (via API) by network ASN
* Using the verbosity flag of the `peeringdb_sync` command will now adjust the logging level
* Expose views to see system, background workers, background queues and background tasks
* [#479](https://github.com/peering-manager/peering-manager/issues/479) Validate BGP community value to make sure that it is a valid community string, this can be disabled by using `VALIDATE_BGP_COMMUNITY_VALUE = False` in the configuration.

### Bug Fixes

* [#526](https://github.com/peering-manager/peering-manager/issues/526) Fix available sessions when having multiple connections on an IXP
* [#840](https://github.com/peering-manager/peering-manager/issues/840) Fix processing of M2M fields during bulk edit to not reset untouched M2M fields
* [#842](https://github.com/peering-manager/peering-manager/issues/842) Fix `missing_sessions` Jinja2 filter, it should now behave the same as long as one of the parameters is a valid
autonomous system object
* [#874](https://github.com/peering-manager/peering-manager/issues/874) Fix `merged_communities` value for BGP sessions with no groups (by @rwielk)
* [#888](https://github.com/peering-manager/peering-manager/issues/888) Keep Django's logs for 500 errors (by @rwielk)
* Fire webhook only if content type matches
* Disable drf-spectacular enum autofix which was throwing warnings for no good reasons
* Improve `missing_sessions` Jinja2 filter to work against PeeringDB network objects, though it will display all possible sessions and not only the missing ones
* Fix IX-API tab not be highlighted when viewing IX-API details for an IXP
* Fix IX-API changelog on authentication refresh
* Fix getting direct peering sessions with an AS with a given group using the `direct_sessions` Jinja2 filter
* Ignore PeeringDB campus <> facility relationships during synchronisation due to PeeringDB API behaviour causing database integrity issues
* Add `name_peeringdb_sync` field to AS REST API data

### Code Housekeeping / Code Quality

* Use [Poetry](https://python-poetry.org/) as main tool for dependency management
* Use [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting
* Raise warning if user sets `PEERINGDB_USERNAME` and/or `PEERINGDB_PASSWORD` instead of using `PEERINGDB_API_KEY`
* Perform code cleanup by enabling Ruff linting rules

### Documentation

* Warn user about e-mail template incompatibility
* New Nokia SR-OS template using Peering Manager extensively (by @rinsekloek)
