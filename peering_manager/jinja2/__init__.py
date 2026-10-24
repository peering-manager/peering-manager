from __future__ import annotations

import traceback

from django.conf import settings
from jinja2 import TemplateSyntaxError

from .extensions import *
from .filters import *
from .functions import *
from .loaders import *
from .sandbox import RestrictedEnvironment


def render_jinja2(template, context, trim=False, lstrip=False):
    """
    Render the template using Jinja2.
    """
    environment = RestrictedEnvironment(loader=PeeringManagerLoader(), trim_blocks=trim, lstrip_blocks=lstrip)
    environment.add_extension(IncludeTemplateExtension)
    for extension in settings.JINJA2_TEMPLATE_EXTENSIONS:
        environment.add_extension(extension)

    # Add custom filters to our environment
    environment.filters.update(FILTER_DICT)
    environment.globals.update(FUNCTION_DICT)

    # Try rendering the template, return a message about syntax issues if there
    # are any
    try:
        jinja2_template = environment.from_string(template)
        return jinja2_template.render(**context)
    except TemplateSyntaxError as e:
        return f"Syntax error in template at line {e.lineno}: {e.message}"
    except Exception:
        return traceback.format_exc()
