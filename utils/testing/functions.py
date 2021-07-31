import json
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

from django.core.exceptions import FieldDoesNotExist
from django.db.models import ManyToManyField
from django.forms.models import model_to_dict as _model_to_dict
from taggit.managers import TaggableManager


def json_file_to_python_type(filename):
    with open(filename, mode="r") as f:
        return json.load(f)


def model_to_dict(instance, fields, api=False):
    """
    Returns a dictionary representation of an instance.
    """
    model_dict = _model_to_dict(instance, fields=fields)

    # Map any additional (non-field) instance attributes that were specified
    for attr in fields:
        if hasattr(instance, attr) and attr not in model_dict:
            model_dict[attr] = getattr(instance, attr)

    for key, value in list(model_dict.items()):
        try:
            field = instance._meta.get_field(key)
        except FieldDoesNotExist:
            continue

        if value and type(field) in (ManyToManyField, TaggableManager):
            model_dict[key] = sorted([o.pk for o in value])

        if api and type(value) in (
            IPv4Address,
            IPv6Address,
            IPv4Interface,
            IPv6Interface,
        ):
            model_dict[key] = str(value)

    return model_dict


def post_data(data):
    """
    Takes a dictionary of test data and returns a dict suitable for POSTing.
    """
    r = {}

    for key, value in data.items():
        if value is None:
            r[key] = ""
        elif type(value) in (list, tuple):
            if value and hasattr(value[0], "pk"):
                # Value is a list of instances
                r[key] = [v.pk for v in value]
            else:
                r[key] = value
        elif hasattr(value, "pk"):
            # Value is an instance
            r[key] = value.pk
        else:
            r[key] = str(value)

    return r
