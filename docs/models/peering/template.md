# Template

Templates are used for rendering device configurations and emails. The template
is parsed using a context processor to complete variable references and execute
control statements.

Inside Peering Manager, templates use the
[Jinja2](https://palletsprojects.com/p/jinja/) syntax which allows for complex
logic building. Different variables are exposed to the Jinja2 processor for
e-mail and configuration templates

Examples of templates are provided in the Peering Manager's
[documentation](https://peering-manager.readthedocs.io/en/latest/templates/).

For each template that you create, the following properties can be configured
(n.b. some are optional):

  * `Name`: human-readable name attached to a template.
  * `Slug`: unique configuration and URL friendly name; usually it is
     automatically generated from the template's name.
  * `Type`: identifies if the template is for device configuration or e-mail.
  * `Template`: the template itself, formatted using Jinja2 syntax.
  * `Comments`: text to explain what the template is for. Can use Markdown
    formatting.
  * `Tags`: a list of tags to help identifying and searching for a template.
