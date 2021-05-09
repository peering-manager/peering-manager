# Templating

Peering Manager comes with a built-in templating feature. This feature can be
used to generate configuration for routers as well as e-mails.

## Jinja2

The templating feature is based on [Jinja2](https://jinja.palletsprojects.com/);
therefore templates must follow Jinja2's syntax. To help you writing your
templates, Peering Manager will expose [variables](variables.md) and
[filters](filters.md).

## Examples

If you need some guidance before writing a template, you can take a look at
the following example templates. Please note these may not be ready to use for
you as they are maintained by the community. However, feel free to use them
and to change them at your convenience.

  * [Juniper Junos](examples/juniper-junos.md)
  * [Cisco IOS-XR](examples/cisco-iosxr.md)
  * [Arista EOS](examples/arista-eos.md)
  * [Peering Request E-mail](examples/peering-request-email.md)
