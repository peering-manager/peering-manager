import platform
import sys

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.utils import formatting

from peering_manager.api.exceptions import SerializerNotFound


def get_serializer_for_model(model, prefix="", suffix=""):
    """
    Returns the appropriate API serializer for a model.
    """
    app_name, model_name = model._meta.label.split(".")
    if app_name == "auth":
        app_name = "users"
    serializer_name = (
        f"{app_name}.api.serializers.{prefix}{model_name}{suffix}Serializer"
    )
    try:
        # Try importing the serializer class
        components = serializer_name.split(".")
        mod = __import__(components[0])
        for c in components[1:]:
            mod = getattr(mod, c)
        return mod
    except AttributeError:
        raise SerializerNotFound(
            f"Could not determine serializer for {app_name}.{model_name} with prefix '{prefix}' and suffix '{suffix}'"
        )


def get_view_name(view, suffix=None):
    """
    Derive the view name from its associated model, if it has one.
    Fall back to DRF's built-in `get_view_name`.
    """
    if hasattr(view, "queryset"):
        # Determine the model name from the queryset
        name = view.queryset.model._meta.verbose_name
        name = " ".join(
            [w[0].upper() + w[1:] for w in name.split()]
        )  # Capitalize each word
    else:
        # Replicate DRF's built-in behavior
        name = view.__class__.__name__
        name = formatting.remove_trailing_string(name, "View")
        name = formatting.remove_trailing_string(name, "ViewSet")
        name = formatting.camelcase_to_spaces(name)

    if suffix:
        name += " " + suffix

    return name


def is_api_request(request):
    """
    Return `True` of the request is being made via the REST API.
    """
    api_path = reverse("api-root")
    return request.path_info.startswith(api_path)


def rest_api_server_error(request, *args, **kwargs):
    """
    Handle exceptions and return a useful error message for REST API requests.
    """
    type_, error, _ = sys.exc_info()
    data = {
        "error": str(error),
        "exception": type_.__name__,
        "peering_manager_version": settings.VERSION,
        "python_version": platform.python_version(),
    }
    return JsonResponse(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
