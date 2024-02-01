# Configuration

Configurations are templates used for rendering device configurations. The
template is parsed using a context processor to complete variable references
and execute control statements.

Inside Peering Manager, templates use the
[Jinja2](https://palletsprojects.com/p/jinja/) syntax which allows for complex
logic building. By default, a single trailing newline is stripped if present
other whitespace (spaces, tabs, newlines etc.) is returned unchanged. You can
tweak this behavior by enabling/disabling the trim and lstrip options.

Examples of configuration are provided in the Peering Manager's
[documentation](../../templating/index.md).

For each configuration that you create, the following properties can be
configured (n.b. some are optional):

* `Name`: human-readable name attached to a template.
* `Slug`: unique configuration and URL friendly name; usually it is
  automatically generated from the configuration's name.
* `Template`: the template itself, formatted using Jinja2 syntax.
* `Jinja2 trim`: if enabled, the first newline after a template tag is removed
  automatically.
* `Jinja2 lstrip`: if enabled, tabs and spaces from the beginning of a line to
  the start of a block will be removed.
* `Comments`: text to explain what the template is for. Can use Markdown
  formatting.
* `Tags`: list of tags to help identifying and searching for a template.
