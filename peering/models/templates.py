from django.urls import reverse
from jinja2 import Environment, TemplateSyntaxError

from .abstracts import Template
from .jinja2 import FILTER_DICT


class Configuration(Template):
    def get_absolute_url(self):
        return reverse("peering:configuration_details", args=[self.pk])

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        environment = Environment(
            trim_blocks=self.jinja2_trim, lstrip_blocks=self.jinja2_lstrip
        )

        # Add custom filters to our environment
        environment.filters.update(FILTER_DICT)

        # Try rendering the template, return a message about syntax issues if there
        # are any
        try:
            jinja2_template = environment.from_string(self.template)
            return jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            return f"Syntax error in template at line {e.lineno}: {e.message}"
        except Exception as e:
            return str(e)
