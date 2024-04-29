from jinja2 import BaseLoader, TemplateNotFound

__all__ = ("PeeringManagerLoader",)


class PeeringManagerLoader(BaseLoader):
    """
    Load templates from the known database objects.
    """

    def _lookup_object(self, kind, identifier):
        """
        Look for an object of a given kind using its identifier and return one of its
        attributes (a template or a rendered template).
        """
        attribute = "template"

        if kind == "configuration":
            from devices.models import Configuration

            model = Configuration
        elif kind == "email":
            from messaging.models import Email

            model = Email
        elif kind == "exporttemplate":
            from extras.models import ExportTemplate

            model = ExportTemplate
            attribute = "rendered"
        else:
            return ""

        try:
            lookup = {"pk": int(identifier)}
        except ValueError:
            lookup = {"name": identifier}

        try:
            o = model.objects.get(**lookup)
        except model.DoesNotExist as e:
            raise TemplateNotFound(identifier) from e

        return getattr(o, attribute)

    def get_source(self, environment, template):
        source = self._lookup_object(*template.split("::", maxsplit=1))
        return source, template, None
