## Version 1.7.1 | MARK I (Bug fixes release) | 2022-08-29

### Bug Fixes

* Fix side menu expansion with export templates
* Remove hardcoded python path from upgrade script
* [#548](https://github.com/peering-manager/peering-manager/issues/548) Always cache dict values for NAPALM neighbors output
* Fix connection edit form
* Use napalm logger for NAPALM related code
* Fix columns in router connections table

## Version 1.7.0 | MARK I (Features release) | 2022-08-21

The 1.7.x releases require Python 3.8 or later as well as PostgreSQL 10 or later.

### New Features

#### API Breaking Changes

1. BGP group `status` field has been added.
2. Internet exchange point `status` field has been added.
3. BGP sessions (direct and IXP) `status` field has been added.
4. BGP sessions (direct and IXP) `enabled` field has been removed (replaced by `status`). Templating will not be broken as an `enabled` property is still exposed (not in the REST API though) which reflects the boolean value of the expression `status == "enabled"`.
5. Router `device_state` field has been renamed to `status`.
6. Connection `state` field has been renamed to `status`.

#### Improve Configuration Contexts ([#567](https://github.com/peering-manager/peering-manager/issues/567))

Configuration contexts used to be a feature restricted to few objects. With this release's improvements, they are available on almost all objects. A new configuration context object is also provided to use common contexts for several objects.

Objects have two levels of contexts. The first level is about config contexts assigned to objects with weights. The second level is the local context data, specific to the object itself. The two levels will be merged into one final context given the `CONFIG_CONTEXT_RECURSIVE_MERGE` and `CONFIG_CONTEXT_LIST_MERGE` settings (possible values are detailed in the documentation).

#### Export Templates

Peering Manager now allows users to define custom templates that can be used when exporting objects. To create an export template, navigate to Others > Export Templates.

Each export template is associated with a certain type of object and uses the Jinja2 templating engine. Therefore all filters available for configuration templates are also available for export templates.

The list of objects returned from the database when rendering an export template is stored in the `dataset` variable, which you'll typically want to iterate through using a for loop. Object properties can be access by name. For example:

```no-highlight
+---------------------------------------------------------------------
| Internet Exchange Points
+---------------------------------------------------------------------
{% for ixp in dataset %}
{{ ixp.name }}
{% for connection in ixp | connections %}
- {{ "{:<15}".format(connection.ipv4_address | ip) }} | {{ connection.ipv6_address | ip }}
{% endfor %}
+---------------------------------------------------------------------
{% endfor %}
```

If you need to use the config context data in an export template, you'll should use the property `config_context` to get all the config context data.

#### Objects Status ([#292](https://github.com/peering-manager/peering-manager/issues/292))

Connections, routers, direct peering sessions and IXP peering sessions have a `status` field indicating their operational state. For sessions, this field replace the old `enabled` field. The `enabled` property is still exposed as part of the templating system (corresponding to a `status` with value `enabled`) but users should start migrating to prepare of its removal in a later release.

As status can be changed at different level, a `inherited_status` Jinja2 filter is introduced to be able to get the status of an object taking into account the one of its parent (if any). For instance, if a connection is disabled but an IXP session attached to it is enabled, the filter will tell that the session is disabled. Also if a connection as a router linked to it and the router is in maintenance status, the session will be considered as in maintenance even if the connection is enabled.

Possible values for `status` are: `enabled`, `maintenance` and `disabled`.

#### New `housekeeping` Command

Object changelog and job results used to be cleanup automatically. This is no longer the case as the code logic has been entirely moved to the new `housekeeping` command. By default, changelog and job results will not be cleaned unless users run the command for it. This command also checks the availability of new releases.

The `housekeeping` command is intended to be run regularly, at any interval users want.

In addition to the command, a new `JOBRESULT_RETENTION` setting, with a default value of 90 days, has been added to allow different retention periods for changelog and job results.

### Enhancements

* Allow `--tasks` flag to `peeringdb_sync` command
* Add `unique` filter for queryset in templates
* Add Jinja2 extensions example in docs
* Display IX-API details on the connection details view
* Synchronise PeeringDB models with 2.39.0
* Remove setting `RELEASE_CHECK_TIMEOUT`, not needed with new `housekeeping` command

### Bug Fixes

* Fix IXP session abandoned state with no router set
* [#613](https://github.com/peering-manager/peering-manager/issues/613) Allow contacts to have the same name
* [#614](https://github.com/peering-manager/peering-manager/issues/614) Make connection filter router aware, sort connections by IXP then by router
