import platform
from collections import OrderedDict

from django import __version__ as DJANGO_VERSION
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.db.models import ProtectedError
from django.http import Http404
from django_rq.queues import get_connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet as __ModelViewSet
from rest_framework.viewsets import ReadOnlyModelViewSet as __ReadOnlyModelViewSet
from rest_framework.viewsets import ViewSet
from rq.worker import Worker

from peering_manager.api.authentication import IsAuthenticatedOrLoginNotRequired
from peering_manager.api.exceptions import SerializerNotFound
from peering_manager.api.serializers import BulkOperationSerializer
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


class BulkDestroyModelMixin:
    """
    Supports bulk deletion of objects using the list endpoint.
    Accepts a DELETE action with a list of one or more JSON objects, each specifying
    the numeric ID of an object to be deleted. For example:
    ```
    DELETE /routers/
    [
        {"id": 123},
        {"id": 456}
    ]
    ```
    """

    def bulk_destroy(self, request, *args, **kwargs):
        serializer = BulkOperationSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        qs = self.get_queryset().filter(pk__in=[o["id"] for o in serializer.data])
        self.perform_bulk_destroy(qs)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_bulk_destroy(self, objects):
        with transaction.atomic():
            for o in objects:
                if hasattr(o, "snapshot"):
                    o.snapshot()
                self.perform_destroy(o)


class BulkUpdateModelMixin:
    """
    Supports bulk modification of objects using the list endpoint.
    Accepts a PATCH action with a list of one or more JSON objects, each specifying
    the numeric ID of an object to be updated as well as the attributes to be set.
    For example:
    ```
    PATCH /routers/
    [
        {
            "id": 123,
            "device_state": "maintenance"
        },
        {
            "id": 456,
            "device_state": "maintenance"
        }
    ]
    ```
    """

    def bulk_update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = BulkOperationSerializer(data=request.data, many=True)

        serializer.is_valid(raise_exception=True)
        qs = self.get_queryset().filter(pk__in=[o["id"] for o in serializer.data])

        # Map update data by object ID
        update_data = {o.pop("id"): o for o in request.data}

        data = self.perform_bulk_update(qs, update_data, partial=partial)

        return Response(data, status=status.HTTP_200_OK)

    def perform_bulk_update(self, objects, update_data, partial):
        with transaction.atomic():
            data_list = []
            for obj in objects:
                data = update_data.get(obj.id)
                if hasattr(obj, "snapshot"):
                    obj.snapshot()

                serializer = self.get_serializer(obj, data=data, partial=partial)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                data_list.append(serializer.data)

            return data_list

    def bulk_partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.bulk_update(request, *args, **kwargs)


class ModelViewSet(BulkDestroyModelMixin, BulkUpdateModelMixin, __ModelViewSet):
    """
    Custom `ModelViewSet` capable of handling either a single object or a list of
    objects to create, update or delete.
    """

    brief = False
    brief_prefetch_fields = []

    def get_object_with_snapshot(self):
        """
        Saves a pre-change snapshot of the object immediately after retrieving it.
        This snapshot will be used to record the "before" data in the changelog.
        """
        o = super().get_object()
        if hasattr(o, "snapshot"):
            o.snapshot()
        return o

    def get_serializer(self, *args, **kwargs):
        # A list is given use `many=True`
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        if self.brief:
            try:
                return get_serializer_for_model(self.queryset.model, prefix="Nested")
            except SerializerNotFound:
                pass

        # Fall back to the hard-coded serializer class
        return self.serializer_class

    def get_queryset(self):
        # If using `brief` mode, clear all prefetches from the queryset and append
        # only `brief_prefetch_fields` (if any)
        if self.brief:
            return (
                super()
                .get_queryset()
                .prefetch_related(None)
                .prefetch_related(*self.brief_prefetch_fields)
            )
        else:
            return super().get_queryset()

    def initialize_request(self, request, *args, **kwargs):
        if request.method == "GET" and request.GET.get("brief"):
            self.brief = True

        return super().initialize_request(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except ProtectedError as e:
            protected_objects = list(e.protected_objects)
            msg = f"Unable to delete object. {len(protected_objects)} dependent objects were found: "
            msg += ", ".join([f"{o} ({o.pk})" for o in protected_objects])
            return self.finalize_response(
                request,
                Response({"detail": msg}, status=status.HTTP_409_CONFLICT),
                *args,
                **kwargs,
            )

    def _validate_objects(self, instance):
        """
        Checks that the provided instance or list of instances are matched by the
        current queryset.
        """
        if type(instance) is list:
            # Check that all instances are still included in the view's queryset
            conforming_count = self.queryset.filter(
                pk__in=[o.pk for o in instance]
            ).count()
            if conforming_count != len(instance):
                raise ObjectDoesNotExist
        else:
            # Check that the instance is matched by the view's queryset
            self.queryset.get(pk=instance.pk)

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save()
                self._validate_objects(instance)
        except ObjectDoesNotExist:
            raise PermissionDenied()

    def update(self, request, *args, **kwargs):
        # Hotwire get_object() to ensure we save a pre-change snapshot
        self.get_object = self.get_object_with_snapshot
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save()
                self._validate_objects(instance)
        except ObjectDoesNotExist:
            raise PermissionDenied()

    def destroy(self, request, *args, **kwargs):
        # Hotwire get_object() to ensure we save a pre-change snapshot
        self.get_object = self.get_object_with_snapshot
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        return super().perform_destroy(instance)


class ReadOnlyModelViewSet(__ReadOnlyModelViewSet):
    """
    Custom ReadOnlyModelViewSet capable of using nested serializers.
    """

    brief = False

    def get_serializer(self, *args, **kwargs):
        # A list is given use `many=True`
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super().get_serializer(*args, **kwargs)

    def get_serializer_class(self):
        if self.brief:
            try:
                return get_serializer_for_model(self.queryset.model, prefix="Nested")
            except SerializerNotFound:
                pass

        # Fall back to the hard-coded serializer class
        return self.serializer_class

    def initialize_request(self, request, *args, **kwargs):
        if request.method == "GET" and request.GET.get("brief"):
            self.brief = True

        return super().initialize_request(request, *args, **kwargs)


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
