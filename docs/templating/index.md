# Templating

Peering Manager comes with a built-in templating feature. This feature can be
used to generate configuration for routers as well as e-mails.

!!! warning
    Even though Peering Manager uses a sandboxed environment to run Jinja2
    logic, the language is powerful enough to do things that can potentially
    leak confidential details or even harm the machine. Be extremely careful
    when using code from someone else.

## Jinja2

The templating feature is based on
[Jinja2](https://jinja.palletsprojects.com/). To simplify template writing,
Peering Manager exposes [variables](variables.md) and [filters](filters.md).
While exposed filters are always the same, variables depends on the context in
which the template is rendered. Rendering a device configuration uses a
context different from the one used when rendering an e-mail.

You can also use Jinja2 extensions by installing them in the Python
environment and asking Peering Manager to load them using the
[`JINJA2_TEMPLATE_EXTENSIONS`](../configuration/system.md#jinja2_template_extensions)
setting.

## CLI

Tests can be performed via a terminal and the `render_configuration` command.
This command must be run from Peering Manager's virtual environment and can
take up to five arguments:

* `--limit [LIMIT]`: limit the configuration to the given set of routers
  (comma separated)
* `--input [INPUT]`: file to read the template from (default to stdin)
* `--output [OUTPUT]`: file to write the configuration to (default to stdout)
* `--trim`: remove new line after tag (keep them by default)
* `--lstrip`: strip whitespaces before block (keep them by default)

For example, to generate the configuration for a device called `router1` from
the standard input and printing it to the standard output, the command to run
will be:

```no-highlight
(venv) # echo '{{ router.hostname }} | python manage.py render_configuration --limit router1
...
```

## Examples

If you need some guidance before writing a template, you can take a look at
the following examples. Please note these may require changes to work as
intended as they are maintained by the community.

* [Juniper Junos](examples/juniper-junos.md)
* [Cisco IOS-XR](examples/cisco-iosxr.md)
* [Cisco IOS-XR as used by AS196610](examples/cisco-iosxr-as196610.md)
* [Cisco IOS-XR from template tutorial](examples/tutorial-cisco-iosxr.md)
* [Cisco IOS from template tutorial](examples/tutorial-cisco-ios.md)
* [Arista EOS](examples/arista-eos.md)
* [Nokia SROS](examples/nokia-sros.md)
* [Peering Request E-mail](examples/peering-request-email.md)
* [New Network E-mail](examples/new-network-email.md)
