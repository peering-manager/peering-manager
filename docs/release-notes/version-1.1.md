# Peering Manager v1.1 Release Notes

## Version 1.1.0 | MARK I (Features release) | 2019-12-08

### New Features

#### E-mailing

Autonomous System contacts can be synchronised from PeeringDB to use them as recipients for e-mails. Some PeeringDB contacts are hidden and cannot be synchronised if the `PEERINGDB_USERNAME` and `PEERINGDB_PASSWORD` are not set in the configuration. For all contacts to be synchronised, clearing the cache then re-synchronising with PeeringDB is required.

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
