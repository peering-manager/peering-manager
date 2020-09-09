# Configuration

Configurations are templates used for rendering device configurations. The
template is parsed using a context processor to complete variable references
and execute control statements.

Inside Peering Manager, templates use the
[Jinja2](https://palletsprojects.com/p/jinja/) syntax which allows for complex
logic building.

Examples of configuration are provided in the Peering Manager's
[documentation](../../../templating).

For each configuration that you create, the following properties can be
configured (n.b. some are optional):

  * `Name`: human-readable name attached to a template.
  * `Slug`: unique configuration and URL friendly name; usually it is
    automatically generated from the configuration's name.
  * `Template`: the template itself, formatted using Jinja2 syntax.
  * `Comments`: text to explain what the template is for. Can use Markdown
    formatting.
  * `Tags`: list of tags to help identifying and searching for a template.
