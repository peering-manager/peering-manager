# Peering Manager v1.5 Release Notes

## Version 1.5.1 | MARK I (Features release) | 2021-11-30

### Bug Fixes

Fix migration failure when multiple direct peering sessions exist.

## Version 1.5.0 | MARK I (Features release) | 2021-11-30

Note: this release removes support for the `DEFAULT_TIMEOUT` parameter under `REDIS` database configuration. Set `RQ_DEFAULT_TIMEOUT` as a global configuration parameter instead.

We would like to thank [DE-CIX](http://www.de-cix.net) for sponsoring this release and helping to bring IX-API as a new feature.

### New Features

#### General API Changes

It is not longer possible to create nested objects in a single request. Users creating related objects by nesting them into the API calls will need to refactor their code to create objects first before using the IDs in final requests. HTML forms have also been disabled as they do not always reflect properly changes to be made. A `display` field provides a string representation of each object. List endpoints provide new operations for bulk deletion and buld update.

API schema, Swagger interface and Redoc interface are exposed in the following paths:

* `/api/schema/` for the schema
* `/api/docs/` for Swagger UI
* `/api/redoc/` for Redoc UI

There are also breaking changes on endpoints to generate e-mails, configurations and pushing them to routers. If you are using an endpoint that does not consist of creating/changing/deleting an object, be sure to review the API docs using either the Swagger or Redoc interfaces to review the changes.

#### IX-API ([#174](https://github.com/peering-manager/peering-manager/issues/174))

After months of development and collaboration with the DE-CIX team, Peering Manager is now able to retrieve data from [IX-API](https://ix-api.net/) instances for IXPs that use this project. It works by creating IX-API objects and assigning them to IXPs instances that are linked to their respective PeeringDB records. When an IXP is properly setup and is assigned an IX-API object, a new IX-API tab will show on the IXP views. It contains data found in the remote IX-API that matches what Peering Manager knows about the IXP. Missing connections to an IXP, if found in IX-API can be setup with few clicks thanks to this feature.

#### BGP Relationships ([#515](https://github.com/peering-manager/peering-manager/issues/515))

BGP relationships are no longer hard-coded and can be defined via the **Other / Relationships** menu item. Relationships are mandatory to define direct peering sessions. Any relationships in use will be preserved when upgrading; fixing names and colours may be required.

### Enhancements

* [#433](https://github.com/peering-manager/peering-manager/issues/433) Allow bulk edit/delete of connections
* Loop over connections to poll sessions instead of looping over routers
* Sync PeeringDB models to 2.11.0.1
* Add `/status` API endpoint
* Record pre-change data on API update/delete

### Bug Fixes

* [#499](https://github.com/peering-manager/peering-manager/issues/499) Change NGINX configuration doc to fix API access
* [#508](https://github.com/peering-manager/peering-manager/issues/508) Handle generator returned by pynetbox
* [#504](https://github.com/peering-manager/peering-manager/issues/504) Allow `NULL` values for AS max prefix
* Fix Junos template example when peer is disabled
* Fix sorting by IP address in peer list
