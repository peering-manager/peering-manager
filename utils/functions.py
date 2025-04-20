import hashlib
import hmac
import json

from django.contrib import messages
from django.core.serializers import serialize
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.html import escape
from django.utils.safestring import mark_safe
from taggit.managers import _TaggableManager

from .templatetags.helpers import title_with_uppers

__all__ = (
    "content_type_identifier",
    "content_type_name",
    "count_related",
    "dict_to_filter_params",
    "generate_signature",
    "get_key_in_hash",
    "get_permission_for_model",
    "handle_protectederror",
    "is_taggable",
    "merge_hash",
    "normalize_querydict",
    "serialize_object",
    "sha256_hash",
    "shallow_compare_dict",
)


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


def normalize_querydict(querydict):
    """
    Converts a `QueryDict` to a normal, mutable dictionary, preserving list values.

        QueryDict('foo=1&bar=2&bar=3&baz=')
    becomes:
        {'foo': '1', 'bar': ['2', '3'], 'baz': ''}

    This function is necessary because `QueryDict` does not provide any built-in
    mechanism which preserves multiple values.
    """
    return {k: v if len(v) > 1 else v[0] for k, v in querydict.lists()}


def generate_signature(data, secret):
    """
    Returns a signature that can be used to verify that the webhook data were not
    altered.
    """
    signature = hmac.new(key=secret.encode("utf8"), msg=data, digestmod=hashlib.sha512)
    return signature.hexdigest()


def sha256_hash(filepath):
    """
    Returns the SHA256 hash of the file at the specified path.
    """
    return hashlib.sha256(filepath.read_bytes())


def is_taggable(instance):
    """
    Returns `True` if the instance can have tags, `False` otherwise.
    """
    return hasattr(instance, "tags") and issubclass(
        instance.tags.__class__, _TaggableManager
    )


def count_related(model, field):
    """
    Returns a `Subquery` suitable for annotating a child object count.
    """
    subquery = Subquery(
        model.objects.filter(**{field: OuterRef("pk")})
        .order_by()
        .values(field)
        .annotate(c=Count("*"))
        .values("c")
    )
    return Coalesce(subquery, 0)


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
        if isinstance(exclude, list | tuple) and key in exclude:
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
            if isinstance(exclude, list | tuple) and key in exclude:
                continue
            difference[key] = second_dict[key]

    return difference


def content_type_name(ct, include_app=True):
    """
    Returns a human-friendly `ContentType` name (e.g. "Peering > Autonomous System").
    """
    try:
        meta = ct.model_class()._meta
        app_label = title_with_uppers(meta.app_config.verbose_name)
        model_name = title_with_uppers(meta.verbose_name)

        if include_app:
            return f"{app_label} > {model_name}"
        return model_name
    except AttributeError:
        # Model no longer exists
        return f"{ct.app_label} > {ct.model}"


def content_type_identifier(ct):
    """
    Return a "raw" `ContentType` identifier string (e.g. "peering.autonomoussystem").
    """
    return f"{ct.app_label}.{ct.model}"


def get_permission_for_model(model, action):
    """
    Resolves the named permission for a given model and action.
    """
    if action not in ("view", "add", "change", "delete"):
        raise ValueError(f"Unsupported action: {action}")

    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"


def handle_protectederror(obj_list, request, e):
    """
    Generates a user-friendly error message in response to a `ProtectedError`
    exception.
    """
    protected_objects = list(e.protected_objects)
    protected_count = (
        len(protected_objects) if len(protected_objects) <= 50 else "More than 50"
    )
    err_message = f"Unable to delete <strong>{', '.join(str(obj) for obj in obj_list)}</strong>. {protected_count} dependent objects were found: "

    # Append dependent objects to error message
    dependent_objects = []
    for dependent in protected_objects[:50]:
        if hasattr(dependent, "get_absolute_url"):
            dependent_objects.append(
                f'<a href="{dependent.get_absolute_url()}">{escape(dependent)}</a>'
            )
        else:
            dependent_objects.append(str(dependent))
    err_message += ", ".join(dependent_objects)

    messages.error(request, mark_safe(err_message))


def get_key_in_hash(hash, key, default=None, recursive=True):
    """
    Returns the key's value and a boolean telling if this value is a default or not.

    The default value, when key is not found, can be adjusted with the `default`
    parameter. The `recursive` parameter controls whether or not to search for the key
    in nested hashes.
    """
    # null or empty hash, no key to lookup
    if hash is None or hash == {}:
        return default, False

    for k, v in hash.items():
        if k == key:
            return v, True

        # Lookup nested hash
        if recursive and isinstance(v, dict):
            value, found = get_key_in_hash(v, key, default=default, recursive=recursive)
            if found:
                return value, True

    return default, False


def merge_hash(a, b, recursive=True, list_merge="replace"):
    """
    Return a new dictionary result of the merges of `b` into `a`, so that keys from
    `b` take precedence over keys from `a`. (`a` and `b` aren't modified)

    This function is inspired by Ansible's `combine` filter.
    """
    if list_merge not in (
        "replace",
        "keep",
        "append",
        "prepend",
        "append_rp",
        "prepend_rp",
    ):
        raise ValueError(
            "merge_hash: 'list_merge' argument can only be equal to 'replace', 'keep', 'append', 'prepend', 'append_rp' or 'prepend_rp'"
        )

    # Check that a and b are dicts
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise ValueError(
            f"Failed to combine variables, expected dicts but got '{type(a)}' and '{type(b)}'"
        )

    # Performance tweak: if a is empty or equal to b, return b
    if a in ({}, b):
        return b.copy()

    # Create a copy of a to avoid modifying it
    a = a.copy()

    # Performance tweak: if no recursion and replace values, use built-in dict's
    # `update`
    if not recursive and list_merge == "replace":
        a.update(b)
        return a

    # Insert each element of b in a, overriding the one in a (as b has higher
    # priority).
    for key, b_value in b.items():
        # `key` isn't in, update a and move on to the next element of b
        if key not in a:
            a[key] = b_value
            continue

        a_value = a[key]

        # Both a's element and b's element are dicts recursively merge them or
        # override depending on the `recursive` argument and move on
        if isinstance(a_value, dict) and isinstance(b_value, dict):
            if recursive:
                a[key] = merge_hash(a_value, b_value, recursive, list_merge)
            else:
                a[key] = b_value
            continue

        # Both a's element and b's element are lists merge them depending on the
        # `list_merge` argument and move on
        if isinstance(a_value, list) and isinstance(b_value, list):
            if list_merge == "replace":
                a[key] = b_value
            elif list_merge == "append":
                a[key] = a_value + b_value
            elif list_merge == "prepend":
                a[key] = b_value + a_value
            elif list_merge == "append_rp":
                # Append all elements from b_value to a_value and remove common ones
                # _rp stands for "remove present"
                a[key] = [i for i in a_value if i not in b_value] + b_value
            elif list_merge == "prepend_rp":
                # Same as 'append_rp' but prepend
                a[key] = b_value + [i for i in a_value if i not in b_value]
            # else 'keep' done by not changing a[key]
            continue

        # Otherwise just override a's element with b's one
        a[key] = b_value

    return a
