from jinja2 import BaseLoader, TemplateNotFound


class PeeringManagerLoader(BaseLoader):
    """
    Load templates from the known database objects.
    """

    def _lookup_object(self, kind, identifier):
        if kind == "configuration":
            from devices.models import Configuration

            model = Configuration
        elif kind == "email":
            from messaging.models import Email

            model = Email
        else:
            return ""

        try:
            lookup = {"pk": int(identifier)}
        except ValueError:
            lookup = {"name": identifier}

        try:
            return model.objects.get(**lookup)
        except model.DoesNotExist:
            raise TemplateNotFound(identifier)

    def get_source(self, environment, template):
        source = self._lookup_object(*template.split("::"))
        return source.template, template, True
