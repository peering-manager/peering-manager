# Peering Manager Configuration

Peering Manager configuration is stored in `peering_manager/configuration.py`.
An example is provided at `peering_manager/configuration.example.py`. You may
copy it and make changes as appropriate. Peering Manager won't run without a
configuration file.

Not all configuration settings are required to be set, only some of them must
be set for Peering Manager to run as expected.

* [Required settings](required-settings.md)
* [Optional settings](optional-settings.md)

## Changing the Configuration

The Peering Manager service must be restarted after changing the configuration
in order for it to take effect:

```no-highlight
# systemctl restart peering-manager
# systemctl restart peering-manager-rqworker
```
