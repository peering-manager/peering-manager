from typing import Any

from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

__all__ = ("SerializerNotFoundError", "ServiceUnavailable", "UnprocessableRequest", "exception_handler")


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, please try again later."


class UnprocessableRequest(APIException):
    status_code = 422
    default_detail = "The request cannot be processed in the current state."


class SerializerNotFoundError(Exception):
    pass


def _as_positional_errors(detail: Any, data: Any = None) -> Any:
    """
    Rewrite the errors a serializer bound to a list reports so that they stay aligned with the
    positions of the entries in the request body.

    Django REST Framework 3.18 reports those errors as a mapping of the position of each failed
    entry to that entry's errors, and omits the entries that validated. Earlier releases reported a
    list with one item per entry, empty for the entries that validated. Keeping the list form keeps
    the response shape stable for the clients that index into it.

    `data` is the part of the request body that `detail` describes. It only gives the number of
    entries, needed to pad the trailing entries that validated.
    """
    if isinstance(detail, dict):
        if detail and all(isinstance(key, int) for key in detail):
            entries = data if isinstance(data, list) else []
            length = max(len(entries), max(detail) + 1)
            return [
                _as_positional_errors(
                    detail.get(index, {}),
                    entries[index] if index < len(entries) else None,
                )
                for index in range(length)
            ]
        return {
            key: _as_positional_errors(value, data.get(key) if isinstance(data, dict) else None)
            for key, value in detail.items()
        }
    if isinstance(detail, list):
        return [_as_positional_errors(item) for item in detail]
    return detail


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = drf_exception_handler(exc, context)

    if response is not None and isinstance(exc, ValidationError):
        request = context.get("request")
        response.data = _as_positional_errors(response.data, getattr(request, "data", None))

    return response
