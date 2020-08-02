# Template

A template is a text that can be parsed using a context processor that will
give a rendered version of the text by completing variable references and
executing control statements.

Inside Peering Manager, templates use the
[Jinja2](https://palletsprojects.com/p/jinja/) syntax which allows for complex
logics building. Depending if the template is for a configuration or an e-mail
different variables will be exposed to the Jinja2 processor.

Examples of templates are provided in the Peering Manager's
[documentation](https://peering-manager.readthedocs.io/en/latest/templates/).

For each template that you create, the following properties are to be provided
(some are however optional):

  * `Name`: a human readable name attached to a template.
  * `Slug`: a unique configuration and URL friendly name; most of the time it
    is automatically generated from the template's name.
  * `Type`: a value that tells if the template is for configurations or
    e-mails.
  * `Template`: an actual text formatted according to the Jinja2 syntax.
  * `Comments`: some text that can be formatted in Markdown to explain what the
    template is for or to use for any other purposes.
  * `Tags`: a list of tags to help identifying and searching for a template.
