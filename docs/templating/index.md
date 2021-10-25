# Templating

Peering Manager comes with a built-in templating feature. This feature can be
used to generate configuration for routers as well as e-mails.

## Jinja2

The templating feature is based on [Jinja2](https://jinja.palletsprojects.com/);
therefore templates must follow Jinja2's syntax. To help you writing your
templates, Peering Manager will expose [variables](variables.md) and
[filters](filters.md).

## CLI

Tests can be performed via a terminal and the `render_configuration` command.
This command must be run from Peering Manager's virtual environment and can
take up to three arguments:

* `--limit [LIMIT]`: limit the configuration to the given set of routers
  (comma separated).
* `--input [INPUT]`: file to read the template from (default to stdin)
* `--output [OUTPUT]`: file to write the configuration to (default to stdout)

For example, to generate the configuration for a device called `router1` from
the standard input and printing it to the standard output, the command to run
will be:

```no-highlight
(venv) # echo '{{ router.hostname }} | python manage.py render_configuration --limit router1
...
```

## Examples

If you need some guidance before writing a template, you can take a look at
the following example templates. Please note these may not be ready to use for
you as they are maintained by the community. However, feel free to use them
and to change them at your convenience.

* [Juniper Junos](examples/juniper-junos.md)
* [Cisco IOS-XR](examples/cisco-iosxr.md)
* [Cisco IOS-XR as used by AS196610](examples/cisco-iosxr-as196610.md)
* [Cisco IOS-XR from template tutorial](examples/tutorial-cisco-iosxr.md)
* [Cisco IOS from template tutorial](examples/tutorial-cisco-ios.md)
* [Arista EOS](examples/arista-eos.md)
* [Peering Request E-mail](examples/peering-request-email.md)
