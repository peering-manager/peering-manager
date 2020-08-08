# E-mail

E-mails are templates used for rendering e-mails. The template
is parsed using a context processor to complete variable references and execute
control statements.

Inside Peering Manager, templates use the
[Jinja2](https://palletsprojects.com/p/jinja/) syntax which allows for complex
logic building.

Examples of e-mails are provided in the Peering Manager's
[documentation](https://peering-manager.readthedocs.io/en/latest/templates/).

For each e-mail that you create, the following properties can be configured
(n.b. some are optional):

  * `Name`: human-readable name attached to a template.
  * `Slug`: unique configuration and URL friendly name; most of the time it
    is automatically generated from the template's name.
  * `Subject`: subject's template, formatted using Jinja2 syntax.
  * `Template`: body's template, formatted using Jinja2 syntax.
  * `Comments`: text to explain what the template is for. Can use Markdown
    formatting.
  * `Tags`: list of tags to help identifying and searching for a template.
