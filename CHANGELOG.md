# Changelog

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

## Version 1.3.2 | MARK I (Bug fixes release) | 2021-01-20

### Enhancements

* Hide PeeringDB related buttons if data are not locally synchronized

### Bug Fixes

* Set local autonomous system on migration in another DB transaction (in another migration file) to fix migration failures
* Fix Internet Exchange import when no affiliated autonomous system is used
* Fix email tab when AS has no contact properties defined but has PeeringDB contacts
* [#346](https://github.com/peering-manager/peering-manager/issues/346) Fix direct session creation from AS view
* [#349](https://github.com/peering-manager/peering-manager/issues/349) Fix e-mail rendering failure, templates may need minor changes

## Version 1.3.1 | MARK I (Bug fixes release) | 2021-01-07

### Enhancements

* Make sure multi-AS migration is passed before PeeringDB's
* Remove PeeringDB synchronization records when upgrading to make sure a full synchronization will be performed next time
* Use `pathlib` in settings instead of `os.join()` to load settings
* [#316](https://github.com/peering-manager/peering-manager/issues/316) Add a tab to see an object changelog when viewing its properties
* [#317](https://github.com/peering-manager/peering-manager/issues/317) Expose changelogs on the REST API

### Bug Fixes

* Fix router filter when using config and password encryption as parameters
* Fix default columns for changelog table which appeared to be empty
* Fix router search when using platform as a parameter
* [#335](https://github.com/peering-manager/peering-manager/issues/335) Keep using `MY_ASN`, the setting, will be removed after 2.0.0, to create automatically the first affiliated AS using the previously configured ASN
* [#339](https://github.com/peering-manager/peering-manager/issues/339) Fix crash when a user has invalid table columns in his/her tables preferences
* [#342](https://github.com/peering-manager/peering-manager/issues/342) Fix BGP sessions import failures due to IP in prefix check issues
* Fix importing IX peering sessions from known PeeringDB peers
* [#344](https://github.com/peering-manager/peering-manager/issues/344) Fix IX search when using local AS name as criteria
* [#345](https://github.com/peering-manager/peering-manager/issues/345) Fix adding IX peering sessions from a PeeringDB peer if the record misses on IP address (IPv4 or IPv6)

## Version 1.3.0 | MARK I (Features release) | 2020-12-22

Take this release as little early Christmas gift. There will be some rough edges to be fixed in bug fixes releases. Please take some time to read the changelog, breaking changes are there.

### New Features

#### Support For Multiple Affiliated Autonomous Systems

This feature has been sponsored by [CIRA - The Canadian Internet Registration Authority](https://www.cira.ca/). Big thanks to them for bringing it to the community.

As of this release users will now be able to manage more than one autonomous systems as their own within a single Peering Manager instance as described in [issue #288](https://github.com/peering-manager/peering-manager/issues/288).

This feature is a big one as it brings some breaking changes to the way users used to define their own autonomous system. Until now a `MY_ASN` setting was required. This setting is dropped in this release but do **not** delete it yet. It will be used for migration purposes while moving from an older release to this one.

After configuring Peering Manager, users have to create at least one autonomous system, their own, and check the new `Affiliated` field to mark the AS. More than one autonomous systems can be marked as affiliated. A dropdown menu will then appear next to the user profile menu so they can select which AS they are working on. This choice is done per-user so two different users can work on two different autonomous systems at the same time. The dropdown menu can also be used to perform a quick switch of context. The last choice will be remembered for later use.

Internet Exchanges, routers and direct peering sessions are linked to a local autonomous system. It means that these objects are "owned" by the local AS. When migrating from a previous version, users' AS will be automatically created and existing objects will be linked to it.

To conclude on this feature, users will need to review their templates due to variable changes.

#### PeeringDB Interaction

To support new features and fix some serious bugs that we tried to manage from one release to the next, the whole code used to fetch data from PeeringDB as been re-written.

During the migration from a previous release, the local PeeringDB cache will be cleared to make a clean slate. Users will need to run `python3 manage.py peeringdb_sync` after upgrading. Be aware that first run can take a lot of time to complete: up to an hour depending on the machine Peering Manager is running on.

This first big refactoring of the codebase does not bring a lot of new features, yet. However, it will fix and bring stability to long lasting issues. It also comes in pair with the new affiliated autonomous systems feature as it required it. If no local synchronization of PeeringDB's data is performed, Peering Manager will assume that PeeringDB is not supposed to be used as data source. This change is intentional and will stay as is. If a local copy of PeeringDB data is found, Internet Exchanges will be automatically linked to their corresponding PeeringDB records when a user will load each IX views. These links between Peering Manager and PeeringDB data cannot be overridden and will be set to `NULL` in the database if PeeringDB's data is deleted during a synchronization. Missing peering sessions will still be detected but dynamically, it can take some time but the result will be cached into Redis. The `check_for_ix_peering_sessions` command has been therefore removed. Users will see a regression in the AS list as the icon showing missing sessions has been removed. This is intended due to performance issue and it might come back in another release.

### Enhancements

* Make sure that Peering Manager can be used with the Python version (3.6 to 3.9)
* Allow sending e-mails using SSL/TLS (by @jpbede)
* Add gunicorn to requirements (by @altf4arnold)
* Remove django-taggit-serializer dependency
* Move changelog logic to signals
* Re-design the login view
* Rewrite object details views using generic code
* [#286](https://github.com/peering-manager/peering-manager/issues/286) Expose Prometheus metrics [see docs](docs/setup/8-prometheus.md) (by @dgjustice)

### Bug Fixes

* [#320](https://github.com/peering-manager/peering-manager/issues/320) Hide NAPALM creds for anonymous users
* [#294](https://github.com/peering-manager/peering-manager/issues/294) Fix bulk direct sessions edit from router view
* [#327](https://github.com/peering-manager/peering-manager/issues/327) Fix error when displaying peers view
* [#315](https://github.com/peering-manager/peering-manager/issues/315) Escape HTML characters when rendering markdown

## Version 1.2.1 | MARK I (Bug fixes release) | 2020-09-10

### Enhancements

* Improve code readability by using enumerations instead of constant lists
* Add brief output to API by using `?brief=1`
* Show Python and Peering Manager versions in error 500
* Expose users and groups API endpoint …
* Rework API based widget to offload complexity to the mixin class as much as possible
* [#276](https://github.com/peering-manager/peering-manager/issues/276) Add threading (`NETBOX_API_THREADING`) and SSL/TLS certification verification (`NETBOX_API_VERIFY_SSL`) when using NetBox API
* Show BGP states a prefix counts in peering session views
* [#279](https://github.com/peering-manager/peering-manager/issues/279) Improve documentation about the `DEBUG` optional setting
* Cleanup unused code

### Bug Fixes

* Fix router filter when using config and password encryption as parameters
* Fix default columns for changelog table which appeared to be empty
* Fix router search when using platform as a parameter
* [#275](https://github.com/peering-manager/peering-manager/issues/275) Make BGP group an optional parameter when searching direct peering sessions
* [#277](https://github.com/peering-manager/peering-manager/issues/277) Fix documentation compilation (by @mngan)

## Version 1.2.0 | MARK I (Features release) | 2020-08-08

Peering Manager is now available in a [dedicated organization](https://github.com/peering-manager).

### New Features

#### RADIUS Authentication

A new RADIUS based authentication backend is now available. It uses the `django-radius` module and requires to create a `radius_config.py` file inside the `peering_manager` directory. Contributed by @mngan.

#### Preview Templates

Configuration and e-mails templates can now be previewed by a click on a single button. This feature is particularly useful when creating templates for the first time as it allows to see if the results match expected ones. If a syntax error occurs during the rendering process, the error message will be displayed to the user for fixing.

#### Caching, Background Tasks And Webhooks

Redis is used a caching technology. This feature can help reducing latencies inside Peering Manager by caching the results of SQL queries which could be executed more than once on the same set of data. Putting the results in Redis will avoid having to run the queries again thus reducing database stress. The new setting `CACHE_TIMEOUT` controls the number of seconds for which the results are kept in cache. A 0 value disables the caching process. The cache is also use to cache whole router configurations to avoid going through the template rendering process that can be quite time consuming for large configurations. A configuration cache value is automatically invalidated if the router is it attached to is changed and/or if the template is changed as well.

Redis is also used as background task scheduling mechanism. The primary use of this feature is sending webhooks when objects are changed inside Peering Manager. A webhook is a request sent to a HTTP(S) endpoint with a payload that includes data about an object and its changes. It can be useful for Peering Manager to notify other tools about what it does. It has been accepted as a solution to [#184](https://github.com/peering-manager/peering-manager/issues/184). Webhooks can be created using the administration interface. The same interface can also be used to see background tasks and their states.

The use of Redis is mandatory as of this version and requires a change of configuration. If Redis is installed on the same machine alongside Peering Manager, the following configuration is enough to get it working.

```python
REDIS = {
    'tasks': {
        'HOST': 'localhost',
        'PORT': 6379,
        'PASSWORD': '',
        'CACHE_DATABASE': 0,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    },
    'caching': {
        'HOST': 'localhost',
        'PORT': 6379,
        'PASSWORD': '',
        'CACHE_DATABASE': 1,
        'DEFAULT_TIMEOUT': 300,
        'SSL': False,
    }
}
```

#### [#199](https://github.com/peering-manager/peering-manager/issues/199) User Preferences

Introduce a model for storing per-user preferences. This feature is now used to keep pagination and table columns preferences. Users can delete recorded preferences using the dedicated tab inside their profiles.

#### [#211](https://github.com/peering-manager/peering-manager/issues/211) Table Columns Preferences

Add user interface elements to toggle and reorder table columns for list views. Each column order is stored as a JSON value in user's preferences. Default columns have been assigned to tables.

The peering session state column has been split into 3 different columns:

* actual state,
* received routes value, and,
* advertised routes value.

This helps to sort sessions based on route metrics and state.

### Configuration And E-mail Refactoring

Two new types of object called `Configuration` and `Email` are available to manage templates dedicated to configurations and e-mails differently. When migrating, foreign keys used to link templates to routers will be preserved.

Leveraging the new `Email` object, the `subject` field has been added to allow users to customize e-mail subjects with the same templating capabilities that are available for the e-mail bodies.

### Enhancements

* Add a brand new logo
* Use Django 3.1
* Make sure that Peering Manager can be used with the Python version (3.6 to 3.8)
* Improve unit testing time using mocking techniques
* Prevent LDAP users from changing their passwords
* [#145](https://github.com/peering-manager/peering-manager/issues/145) Notify privileged users when a new version of Peering Manager is available
* [#92](https://github.com/peering-manager/peering-manager/issues/92) Allow user to hide available peers at IXPs; peers can still be displayed using the filter form
* [#197](https://github.com/peering-manager/peering-manager/issues/197) The `grab_prefixes` command can be used to cache prefix list for each AS in the database; a `--limit <0-n>` option [#209](https://github.com/peering-manager/peering-manager/issues/209) is available to avoid caching prefix list exceeding a given number of entries
* Try to guess if a BGP session has been abandoned; if a session, with an AS, on an IXP, both having PeeringDB records, is down, the session will be considered as abandoned
* Add an API call to poll a single BGP session
* Automatically set the local peer ASN for direct peering session
* Set the boundaries of `ASNField` to what AS number can actually be
* Enforce *view* permission to see details about some objects if the `LOGIN_REQUIRED` setting is enabled
* Try guessing the default timezone and defaults to `UTC` in case of failure if the `TIME_ZONE` setting is not set (by @mxhob1)
* [#206](https://github.com/peering-manager/peering-manager/issues/206) Allow configuration to be installed on routers without having to check for differences
* Make sure there are configuration differences to install before connecting to a router
* Remove `py-gfm` requirement as it is no longer maintained
* Only preload selected option for API based select widget; it avoids having to load huge chunks of data by leveraging the API
* Improve template generation time (by @mngan)
* [#244](https://github.com/peering-manager/peering-manager/issues/244) Allow entities to be filtered by tags; when several tags are given, a logical *and* operation will be performed, thus matching entities having all tags requested
* Add peering session lists from router and Internet exchange points of view (by @mngan)
* Improve peering sessions sorting (by @mngan)
* [#181](https://github.com/peering-manager/peering-manager/issues/181) Add fields to allow per-router NAPALM credentials and options (feature based on the idea of @smaxx1337)
* [#253](https://github.com/peering-manager/peering-manager/issues/253) Replace *supervisor* with *systemd* in the documentation
* Use signals to update session passwords to improve reliability of their encrypted versions
* Install configurations on several routers using background tasks; a confirmation is asked to the user but no syntax checks are performed
* Add `slug` field to `Community`; field is meant to be used as a configuration friendly value
* Turn-off validators on community value field as they can be expressed differently depending on router softwares
* [#259](https://github.com/peering-manager/peering-manager/issues/259) Documentation for each type of object is now available in the user interface when creating/editing an object; a small button help button is available in the top bar

### Bug Fixes

* [#196](https://github.com/peering-manager/peering-manager/issues/196) Sort missing peering sessions using their IP families. They are exposedin templates like: `{{ missing_sessions.ipv6 }}` and `{{ missing_sessions.ipv4 }}`
* [#208](https://github.com/peering-manager/peering-manager/issues/208) Fix creating a new BGP session using PeeringDB; if a session is alreadycreated for a PeeringDB record, do not fail add the other one attached to the same record
* [#212](https://github.com/peering-manager/peering-manager/issues/212) Default to "any" IP family match when searching for routing policies
* [#217](https://github.com/peering-manager/peering-manager/issues/217) If bgpq3 exits with a non-zero status code when looking for an AS-SETtry to perform the same lookup with the AS object instead
* [#215](https://github.com/peering-manager/peering-manager/issues/215) Update encrypted passwords when clear ones change
* [#221](https://github.com/peering-manager/peering-manager/issues/221) Remove duplicates from missing peering sessions in templates
* [#190](https://github.com/peering-manager/peering-manager/issues/190) Add the possibility to ignore the name of an AS during PeeringDBsynchronizations
* [#235](https://github.com/peering-manager/peering-manager/issues/235) Add documentation to move the PostgreSQL database to UTF-8 encoding
* [#214](https://github.com/peering-manager/peering-manager/issues/214) Fix router tags usage in templates
* [#251](https://github.com/peering-manager/peering-manager/issues/251) Add routing policies columns for eligible model lists
* [#265](https://github.com/peering-manager/peering-manager/issues/265) Fix broken bulk edit of BGP sessions in a group
* [#268](https://github.com/peering-manager/peering-manager/issues/268) Fix broken view permissions for guests when `LOGIN_REQUIRED` is not set

## Version 1.1.0 | MARK I (Features release) | 2019-12-08

### New Features

#### E-mailing

Autonomous System contacts can be synchronized from PeeringDB to use them as recipients for e-mails. Some PeeringDB contacts are hidden and cannot be synchronized if the `PEERINGDB_USERNAME` and `PEERINGDB_PASSWORD` are not set in the configuration. For all contacts to be synchronized, clearing the cache then re-synchronizing with PeeringDB is required.

[//]: # (The links in the next line are broken.)
When a contact is available for an Autonomous System a `Send E-mail` tab will be available from the AS view. An e-mail template has to be selected along with a contact to send the e-mail to. E-mail templates can be written following [this section](https://peering-manager.readthedocs.io/en/latest/templates/#e-mail) of the documentation. An example is also [available](https://peering-manager.readthedocs.io/en/latest/templates/peering-request-email/).

### Enhancements

* [#191](https://github.com/peering-manager/peering-manager/issues/191) - Bulk edit, bulk delete Internet Exchange peering sessions fromAutonomous System view
* Code testing against Python 3.8
* [#187](https://github.com/peering-manager/peering-manager/issues/187) - Mock external APIs, softwares and e-mails for unit tests
* Add configuration options `PEERINGDB_USERNAME` and `PEERINGDB_PASSWORD` for PeeringDB credentials
* Update Bootstreap CSS to v4.4.1
* Update Select2 to v4.0.12

### Bug Fixes

* [#185](https://github.com/peering-manager/peering-manager/issues/185) - Fix adding the same peering sessions on more than one Internet Exchange
* Fix version string in the user interface

## Version 1.0.0 | MARK I (First release) | 2019-11-13

* First release of Peering Manager
