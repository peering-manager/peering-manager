from jinja2 import nodes
from jinja2.ext import Extension

__all__ = ("IncludeTemplateExtension",)

KINDS = ("configuration", "email", "exporttemplate")


class IncludeTemplateExtension(Extension):
    """
    Add `include_$type`, `import_$type` and `from_$type` tags to Jinja that
    work like `include`, `import` and `from ... import` but lookup objects
    inside the database.
    """

    tags = {
        f"{prefix}_{kind}" for prefix in ("include", "import", "from") for kind in KINDS
    }

    def parse(self, parser):
        token = next(parser.stream)
        tag = token.value
        template_expr = parser.parse_expression()

        if tag.startswith("include_"):
            return self._parse_include(tag[8:], parser, token, template_expr)
        if tag.startswith("import_"):
            return self._parse_import(tag[7:], parser, token, template_expr)
        return self._parse_from_import(tag[5:], parser, token, template_expr)

    def _resolve_template(self, kind, template_expr, raw=False):
        identifier = getattr(template_expr, "name", getattr(template_expr, "value", ""))
        if raw:
            kind = f"{kind}.raw"
        return nodes.Const(f"{kind}::{identifier}")

    def _parse_include(self, kind, parser, token, template_expr):
        node = nodes.Include(lineno=token.lineno)
        node.template = self._resolve_template(kind, template_expr)
        node.ignore_missing = False
        node.with_context = True
        return node

    def _parse_import(self, kind, parser, token, template_expr):
        parser.stream.expect("name:as")
        target = parser.parse_assign_target(name_only=True).name

        node = nodes.Import(lineno=token.lineno)
        node.template = self._resolve_template(kind, template_expr, raw=True)
        node.target = target
        node.with_context = False
        return node

    def _parse_from_import(self, kind, parser, token, template_expr):
        parser.stream.expect("name:import")

        names = []
        while True:
            if names:
                parser.stream.expect("comma")
            if parser.stream.current.type != "name":
                parser.stream.expect("name")
            target = parser.parse_assign_target(name_only=True)
            if parser.stream.skip_if("name:as"):
                alias = parser.parse_assign_target(name_only=True)
                names.append((target.name, alias.name))
            else:
                names.append(target.name)
            if parser.stream.current.type != "comma":
                break

        node = nodes.FromImport(lineno=token.lineno)
        node.template = self._resolve_template(kind, template_expr, raw=True)
        node.names = names
        node.with_context = False
        return node
