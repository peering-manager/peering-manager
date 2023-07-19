from django.db import models

__all__ = ("custom_deconstruct",)


EXEMPT_ATTRS = ("choices", "help_text", "verbose_name")

_deconstruct = models.Field.deconstruct


def custom_deconstruct(field):
    """
    Imitate the behavior of the stock `deconstruct()` method, but ignore the field
    attributes listed above.
    """
    name, path, args, kwargs = _deconstruct(field)

    # Remove any ignored attributes
    for attr in EXEMPT_ATTRS:
        kwargs.pop(attr, None)

    return name, path, args, kwargs
