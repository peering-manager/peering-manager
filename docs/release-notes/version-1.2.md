# Peering Manager v1.2 Release Notes

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
