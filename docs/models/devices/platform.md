# Platform

A platform describes the network operating system of a device and therefore how
to connect to it.

## In Peering Manager

Inside Peering Manager, you create platforms and use them when creating
routers. They will be used as indicator for processes that need to connect to
devices to install configurations or retrieve operational states.

  * `Name`: name of the platform, must be unique.
  * `Slug`: unique URL friendly name; usually it is automatically generated
    from the platform's name.
  * `NAPALM Driver`: identifier of the driver to use; it can be a NAPALM core
    [driver](https://napalm.readthedocs.io/en/latest/support/index.html) or a
    community maintained one.
  * `NAPALM Args`: [optional arguments](https://napalm.readthedocs.io/en/latest/support/index.html#optional-arguments)
    used to change how connections to devices will be established and used.
  * `Password Algorithm`: algorithm used to encrypt password in router
    configuration.
  * `Description`: free text to add details.
