# Peering Manager Configuration

## Configuration File

Peering Manager's configuration file contains all the important parameters
which control how Peering Manager functions: database settings, security
controls, and so on. While the default configuration suffices out of the box
for most use cases, there are a few 
required parameters](./required-parameters.md) which **must** be defined
during installation. 

The configuration file is loaded from
`$INSTALL_ROOT/peering_manager/configuration.py` by default. An example
configuration is provided at `configuration_example.py`, which you may copy to
use as your default config. Note that a configuration file must be defined;
Peering Manager will not run without one.

!!! info "Customising the Configuration Module"
    A custom configuration module may be specified by setting the
    `PEERINGMANAGER_CONFIGURATION` environment variable. This must be a dotted
    path to the desired Python module. For example, a file named
    `my_config.py` in the same directory as `settings.py` would be referenced
    as `peering_manager.my_config`.

    To keep things simple, the Peering Manager documentation refers to the
    configuration file simply as `configuration.py`.

## Modifying the Configuration

The configuration file may be modified at any time. However, the WSGI service
(e.g. Gunicorn) must be restarted before these changes will take effect:

```no-highlight
# systemctl restart peering-manager
# systemctl restart peering-manager-rqworker@1
```
