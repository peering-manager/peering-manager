import platform
from collections import OrderedDict

from django import __version__ as DJANGO_VERSION
from django.apps import apps
from django.conf import settings
from django.http import Http404
from django_rq.queues import get_connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet as __ModelViewSet
from rest_framework.viewsets import ReadOnlyModelViewSet as __ReadOnlyModelViewSet
from rest_framework.viewsets import ViewSet
from rq.worker import Worker

from peering_manager.api.authentication import IsAuthenticatedOrLoginNotRequired
from utils.api import get_serializer_for_model


class APIRootView(APIView):
    _ignore_model_permissions = True
    exclude_from_schema = True

    @staticmethod
    def get_namespace(name, request, format):
        return (
            name,
            reverse(f"{name}-api:api-root", request=request, format=format),
        )

    def get_view_name(self):
        return "API Root"

    def get(self, request, format=None):
        return Response(
            OrderedDict(
                (
                    APIRootView.get_namespace("devices", request, format),
                    APIRootView.get_namespace("extras", request, format),
                    APIRootView.get_namespace("net", request, format),
                    APIRootView.get_namespace("peering", request, format),
                    APIRootView.get_namespace("peeringdb", request, format),
                    APIRootView.get_namespace("users", request, format),
                    APIRootView.get_namespace("utils", request, format),
                )
            )
        )


class StatusView(APIView):
    """
    A lightweight read-only endpoint for conveying NetBox's current operational status.
    """

    permission_classes = [IsAuthenticatedOrLoginNotRequired]

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
        installed_apps = {k: v for k, v in sorted(installed_apps.items())}

        return Response(
            {
                "django-version": DJANGO_VERSION,
                "installed-apps": installed_apps,
                "peering-manager-version": settings.VERSION,
                "python-version": platform.python_version(),
                "rq-workers-running": Worker.count(get_connection("default")),
            }
        )


class ModelViewSet(__ModelViewSet):
    """
    Custom ModelViewSet capable of handling either a single object or a list of objects
    to create.
    """

    def get_serializer(self, *args, **kwargs):
        # A list is given so use many=True
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        request = self.get_serializer_context()["request"]
        if request.query_params.get("brief"):
            try:
                return get_serializer_for_model(self.queryset.model, prefix="Nested")
            except Exception:
                pass

        # Fall back to the hard-coded serializer class
        return self.serializer_class

    def list(self, *args, **kwargs):
        """
        For caching purpose.
        """
        return super().list(*args, **kwargs)

    def retrieve(self, *args, **kwargs):
        """
        For caching purpose.
        """
        return super().retrieve(*args, **kwargs)


class ReadOnlyModelViewSet(__ReadOnlyModelViewSet):
    """
    Custom ReadOnlyModelViewSet capable of using nested serializers.
    """

    def get_serializer(self, *args, **kwargs):
        # A list is given so use many=True
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        request = self.get_serializer_context()["request"]
        if request.query_params.get("brief"):
            try:
                return get_serializer_for_model(self.queryset.model, prefix="Nested")
            except Exception:
                pass

        # Fall back to the hard-coded serializer class
        return self.serializer_class

    def list(self, *args, **kwargs):
        """
        For caching purpose.
        """
        return super().list(*args, **kwargs)

    def retrieve(self, *args, **kwargs):
        """
        For caching purpose.
        """
        return super().retrieve(*args, **kwargs)


class StaticChoicesViewSet(ViewSet):
    """
    Expose values representing static choices for model fields.
    """

    permission_classes = [AllowAny]
    fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fields = OrderedDict()

        for model, field_list in self.fields:
            for field_name in field_list:
                model_name = model._meta.verbose_name.lower().replace(" ", "-")
                key = ":".join([model_name, field_name])
                choices = []
                for k, v in model._meta.get_field(field_name).choices:
                    if type(v) in [list, tuple]:
                        for k2, v2 in v:
                            choices.append({"value": k2, "label": v2})
                    else:
                        choices.append({"value": k, "label": v})
                self._fields[key] = choices

    def list(self, request):
        return Response(self._fields)

    def retrieve(self, request, pk):
        if pk not in self._fields:
            raise Http404
        return Response(self._fields[pk])

    def get_view_name(self):
        return "Static Choices"
