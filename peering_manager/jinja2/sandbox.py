from __future__ import annotations

from typing import Any

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.utils import CursorWrapper
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet, RawQuerySet
from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.query import Query
from jinja2.sandbox import SandboxedEnvironment, SecurityError

__all__ = ("RestrictedEnvironment", "is_unsafe_attribute", "safe_getattr")

# Gateways to raw SQL, blocked by type whatever name points to them
UNSAFE_ATTRIBUTE_TYPES = (Query, SQLCompiler, BaseDatabaseWrapper, CursorWrapper, RawQuerySet)
# Raw SQL methods not flagged `alters_data`
UNSAFE_ORM_METHODS = frozenset({"raw", "extra"})

_MISSING = object()


def is_unsafe_attribute(obj: object, attr: str, value: object) -> bool:
    """The database-layer rule, added on top of Jinja2's own attribute checks."""
    if isinstance(value, UNSAFE_ATTRIBUTE_TYPES):
        return True
    return attr in UNSAFE_ORM_METHODS and isinstance(obj, (BaseManager, QuerySet))


class RestrictedEnvironment(SandboxedEnvironment):
    """Jinja2 sandbox that also hides the database access layer."""

    def is_safe_attribute(self, obj: object, attr: str, value: object) -> bool:
        if is_unsafe_attribute(obj, attr, value):
            return False
        return super().is_safe_attribute(obj, attr, value)


_sandbox = RestrictedEnvironment()


def safe_getattr(obj: object, name: str, default: Any = _MISSING) -> Any:
    """Like `getattr`, but enforces the sandbox's attribute rules."""
    value = getattr(obj, name, _MISSING)

    if value is _MISSING:
        if default is _MISSING:
            raise AttributeError(name)
        return default

    if not _sandbox.is_safe_attribute(obj, name, value):
        raise SecurityError(f"access to attribute {name!r} of {type(obj).__name__!r} object is unsafe.")

    return value
