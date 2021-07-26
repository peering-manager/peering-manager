import hashlib
import hmac
import json

from django.core.serializers import serialize
from taggit.managers import _TaggableManager


# Shamlessly stolen from django.utils.functional (<3.0)
def curry(_curried_func, *args, **kwargs):
    def _curried(*moreargs, **morekwargs):
        return _curried_func(*args, *moreargs, **{**kwargs, **morekwargs})

    return _curried


def dict_to_filter_params(d, prefix=""):
    """
    Flattens a dictionary of attributes to a set of parameters suitable for filtering
    a `QuerySet` that uses `__` as separator.
    """
    params = {}

    for key, val in d.items():
        k = prefix + key
        if isinstance(val, dict):
            params.update(dict_to_filter_params(val, k + "__"))
        else:
            params[k] = val

    return params


def generate_signature(data, secret):
    """
    Returns a signature that can be used to verify that the webhook data were not
    altered.
    """
    signature = hmac.new(key=secret.encode("utf8"), msg=data, digestmod=hashlib.sha512)
    return signature.hexdigest()


def is_taggable(instance):
    """
    Returns `True` if the instance can have tags, `False` otherwise.
    """
    if hasattr(instance, "tags"):
        if issubclass(instance.tags.__class__, _TaggableManager):
            return True
    return False


def serialize_object(instance, extra=None, exclude=None):
    """
    Return a generic JSON representation of an object using Django's built-in
    serializer (not the REST API). Private fields (prefixed with a _) are always
    excluded. Other fields can be excluded to by using the `exclude` list/dictionary.
    """
    json_string = serialize("json", [instance])
    data = json.loads(json_string)[0]["fields"]

    if is_taggable(instance):
        tags = getattr(instance, "_tags", instance.tags.all())
        data["tags"] = [tag.name for tag in tags]

    # Append any extra data
    if extra is not None:
        data.update(extra)

    # Copy keys to list to avoid changing dict size exception
    for key in list(data):
        # Private fields shouldn't be logged in the object change
        if isinstance(key, str) and key.startswith("_"):
            data.pop(key)

        # Explicitly excluded keys
        if isinstance(exclude, (list, tuple)) and key in exclude:
            data.pop(key)

    return data


def shallow_compare_dict(first_dict, second_dict, exclude=None):
    """
    Return a new dictionary with the different key/value pairs found between the first
    and the second dicts. Only the equality of the first layer of keys/values is
    checked. `exclude` is a list or tuple of keys to be ignored. The values from the
    second dict are used in the return value.
    """
    difference = {}

    for key in second_dict:
        if first_dict.get(key) != second_dict[key]:
            if isinstance(exclude, (list, tuple)) and key in exclude:
                continue
            difference[key] = second_dict[key]

    return difference
