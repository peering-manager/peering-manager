import platform
from collections import OrderedDict

from django import __version__ as django_version
from django.apps import apps
from django.conf import settings
from django_rq.queues import get_connection
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rq.worker import Worker

from peering_manager.api.authentication import IsAuthenticatedOrLoginNotRequired

__all__ = ("APIRootView", "StatusView")


class APIRootView(APIView):
    _ignore_model_permissions = True

    @staticmethod
    def get_namespace(name, request, format):
        return (name, reverse(f"{name}-api:api-root", request=request, format=format))

    def get_view_name(self):
        return "API Root"

    @extend_schema(exclude=True)
    def get(self, request, format=None):
        return Response(
            OrderedDict(
                (
                    APIRootView.get_namespace("bgp", request, format),
                    APIRootView.get_namespace("core", request, format),
                    APIRootView.get_namespace("devices", request, format),
                    APIRootView.get_namespace("extras", request, format),
                    APIRootView.get_namespace("messaging", request, format),
                    APIRootView.get_namespace("net", request, format),
                    APIRootView.get_namespace("peering", request, format),
                    APIRootView.get_namespace("peeringdb", request, format),
                    APIRootView.get_namespace("users", request, format),
                    ("status", reverse("api-status", request=request, format=format)),
                )
            )
        )


class StatusView(APIView):
    """
    A lightweight read-only endpoint for conveying Peering Manager's current
    operational status.
    """

    permission_classes = [IsAuthenticatedOrLoginNotRequired]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Details regarding Peering Manager status.",
            )
        },
    )
    def get(self, request):
        # Gather the version numbers from all installed Django apps
        installed_apps = {}
        for app_config in apps.get_app_configs():
            app = app_config.module
            version = getattr(app, "VERSION", getattr(app, "__version__", None))
            if version:
                if type(version) is tuple:
                    version = ".".join(str(n) for n in version)
                installed_apps[app_config.name] = version
        installed_apps = dict(sorted(installed_apps.items()))

        return Response(
            {
                "django-version": django_version,
                "installed-apps": installed_apps,
                "peering-manager-version": settings.VERSION,
                "python-version": platform.python_version(),
                "rq-workers-running": Worker.count(get_connection("default")),
            }
        )
