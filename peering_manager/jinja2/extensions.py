from jinja2 import nodes
from jinja2.ext import Extension

__all__ = ("IncludeTemplateExtension",)


class IncludeTemplateExtension(Extension):
    """
    Add `include_$type` tags to Jinja that work like `include` but lookup objects
    inside the database.
    """

    tags = {"include_configuration", "include_email", "include_exporttemplate"}

    def __init__(self, environment):
        super().__init__(environment)

    def parse(self, parser):
        token = next(parser.stream)
        template = parser.parse_expression()
        identifier = getattr(template, "name", getattr(template, "value", ""))

        # Create an include node for Jinja to parse it and properly import the
        # template. It won't interpret it if we just use an output node instead.
        node = nodes.Include(lineno=token.lineno)
        node.template = nodes.Const(f"{token.value[8:]}::{identifier}")
        node.ignore_missing = False
        node.with_context = True

        return node
