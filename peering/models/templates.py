from django.db import models
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


class Email(Template):
    # While a line length should not exceed 78 characters (as per RFC2822), we allow
    # user more characters for templating and let the user to decide what he wants to
    # with this recommended limit, including not respecting it
    subject = models.CharField(max_length=512)

    def get_absolute_url(self):
        return reverse("peering:email_details", args=[self.pk])

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        subject, body = "", ""
        environment = Environment(
            trim_blocks=self.jinja2_trim, lstrip_blocks=self.jinja2_lstrip
        )

        # Add custom filters to our environment
        environment.filters.update(FILTER_DICT)

        try:
            jinja2_template = environment.from_string(self.subject)
            subject = jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            subject = (
                f"Syntax error in subject template at line {e.lineno}: {e.message}"
            )
        except Exception as e:
            subject = str(e)

        try:
            jinja2_template = environment.from_string(self.template)
            body = jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            body = f"Syntax error in body template at line {e.lineno}: {e.message}"
        except Exception as e:
            body = str(e)

        return subject, body
