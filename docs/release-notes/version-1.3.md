# Peering Manager v1.3 Release Notes

## Version 1.3.2 | MARK I (Bug fixes release) | 2021-01-20

### Enhancements

* Hide PeeringDB related buttons if data are not locally synchronised

### Bug Fixes

* Set local autonomous system on migration in another DB transaction (in another migration file) to fix migration failures
* Fix Internet Exchange import when no affiliated autonomous system is used
* Fix email tab when AS has no contact properties defined but has PeeringDB contacts
* [#346](https://github.com/peering-manager/peering-manager/issues/346) Fix direct session creation from AS view
* [#349](https://github.com/peering-manager/peering-manager/issues/349) Fix e-mail rendering failure, templates may need minor changes

## Version 1.3.1 | MARK I (Bug fixes release) | 2021-01-07

### Enhancements

* Make sure multi-AS migration is passed before PeeringDB's
* Remove PeeringDB synchronisation records when upgrading to make sure a full synchronisation will be performed next time
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

This first big refactoring of the codebase does not bring a lot of new features, yet. However, it will fix and bring stability to long lasting issues. It also comes in pair with the new affiliated autonomous systems feature as it required it. If no local synchronisation of PeeringDB's data is performed, Peering Manager will assume that PeeringDB is not supposed to be used as data source. This change is intentional and will stay as is. If a local copy of PeeringDB data is found, Internet Exchanges will be automatically linked to their corresponding PeeringDB records when a user will load each IX views. These links between Peering Manager and PeeringDB data cannot be overridden and will be set to `NULL` in the database if PeeringDB's data is deleted during a synchronisation. Missing peering sessions will still be detected but dynamically, it can take some time but the result will be cached into Redis. The `check_for_ix_peering_sessions` command has been therefore removed. Users will see a regression in the AS list as the icon showing missing sessions has been removed. This is intended due to performance issue and it might come back in another release.

### Enhancements

* Make sure that Peering Manager can be used with the Python version (3.6 to 3.9)
* Allow sending e-mails using SSL/TLS (by @jpbede)
* Add gunicorn to requirements (by @altf4arnold)
* Remove django-taggit-serializer dependency
* Move changelog logic to signals
* Re-design the login view
* Rewrite object details views using generic code
* [#286](https://github.com/peering-manager/peering-manager/issues/286) Expose Prometheus metrics [see docs](../integrations/prometheus-metrics.md) (by @dgjustice)

### Bug Fixes

* [#320](https://github.com/peering-manager/peering-manager/issues/320) Hide NAPALM creds for anonymous users
* [#294](https://github.com/peering-manager/peering-manager/issues/294) Fix bulk direct sessions edit from router view
* [#327](https://github.com/peering-manager/peering-manager/issues/327) Fix error when displaying peers view
* [#315](https://github.com/peering-manager/peering-manager/issues/315) Escape HTML characters when rendering markdown
