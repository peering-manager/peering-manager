#!.venv/bin/python

import django
import jinja2
import os
import sys

sys.path.append(".")
os.environ["DJANGO_SETTINGS_MODULE"] = "peering_manager.settings"
django.setup()

from django.db.models.fields import (
    AutoField,
    BigIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    TextField,
)
from django.db.models.fields.related import ForeignKey, ManyToManyField
from netfields import InetAddressField
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)
from taggit.managers import TaggableManager


DOC_PATH = "docs/templates/objects"
DOC_TEMPLATE = """# {{ object_name }}

## Usable Variables
{% for variable in variables %}
  * {{ variable }}
{%- endfor %}

"""


def get_model_variables(model):
    variables = []

    for field in model._meta.concrete_fields + model._meta.many_to_many:
        variable = None

        if isinstance(field, ForeignKey):
            variable = "`{}`: {} object".format(
                field.name, get_model_file_link(field.related_model)
            )
        elif isinstance(field, ManyToManyField):
            variable = "`{}`: list of {} objects".format(
                field.name, get_model_file_link(field.related_model)
            )
        elif isinstance(field, TaggableManager):
            variable = "`{}`: list of tags".format(field.name)
        else:
            field_type = None
            if isinstance(field, BooleanField):
                field_type = "boolean"
            elif isinstance(field, CharField):
                field_type = "string"
            elif isinstance(field, TextField):
                field_type = "text"
            elif isinstance(field, DateTimeField):
                field_type = "date"
            elif isinstance(field, InetAddressField):
                field_type = "IP address"
            elif (
                isinstance(field, AutoField)
                or isinstance(field, BigIntegerField)
                or isinstance(field, PositiveIntegerField)
                or isinstance(field, PositiveSmallIntegerField)
            ):
                field_type = "integer".format(field.name)
            else:
                print(
                    "Unknown type for `{}`: {}".format(
                        field.name, field.get_internal_type()
                    )
                )

            if field_type:
                variable = "`{}`: {} value".format(field.name, field_type)

        if variable:
            variables.append(variable)

    return variables


def get_model_file_name(model):
    return "{}/{}.md".format(DOC_PATH, model._meta.model_name)


def get_model_file_link(model):
    return "[{}]({}.md)".format(model._meta.object_name, model._meta.model_name)


def generate_doc_page(model):
    filename = get_model_file_name(model)
    doc = (
        jinja2.Environment()
        .from_string(DOC_TEMPLATE)
        .render(
            object_name=model._meta.object_name, variables=get_model_variables(model)
        )
    )

    with open(get_model_file_name(model), "w") as f:
        f.write(doc)


if __name__ == "__main__":
    for model in [
        AutonomousSystem,
        BGPGroup,
        Community,
        DirectPeeringSession,
        InternetExchange,
        InternetExchangePeeringSession,
        Router,
        RoutingPolicy,
    ]:
        generate_doc_page(model)
