import logging

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.db.models import ProtectedError
from rest_framework import mixins as drf_mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from utils.exceptions import AbortRequest

from . import mixins

__all__ = ("PeeringManagerReadOnlyModelViewSet", "PeeringManagerModelViewSet")


class BaseViewSet(GenericViewSet):
    """
    Base class for all API ViewSets.

    It is currently an empty shell, but it might become useful in the future to add
    common logics to all view sets.
    """


class PeeringManagerReadOnlyModelViewSet(
    mixins.BriefModeMixin,
    mixins.ExportTemplatesMixin,
    drf_mixins.RetrieveModelMixin,
    drf_mixins.ListModelMixin,
    BaseViewSet,
):
    pass


class PeeringManagerModelViewSet(
    mixins.BulkUpdateModelMixin,
    mixins.BulkDestroyModelMixin,
    mixins.ObjectValidationMixin,
    mixins.BriefModeMixin,
    mixins.ExportTemplatesMixin,
    drf_mixins.CreateModelMixin,
    drf_mixins.RetrieveModelMixin,
    drf_mixins.UpdateModelMixin,
    drf_mixins.DestroyModelMixin,
    drf_mixins.ListModelMixin,
    BaseViewSet,
):
    """
    Extend DRF's `ModelViewSet` to support bulk update and delete functions.
    """

    def get_object_with_snapshot(self):
        """
        Save a pre-change snapshot of the object immediately after retrieving it. This
        snapshot will be used to record the "before" data in the changelog.
        """
        obj = super().get_object()
        if hasattr(obj, "snapshot"):
            obj.snapshot()
        return obj

    def get_serializer(self, *args, **kwargs):
        # If a list of objects has been provided, initialize the serializer with many=True
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True

        return super().get_serializer(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        logger = logging.getLogger(
            f"peering_manager.api.views.{self.__class__.__name__}"
        )

        try:
            return super().dispatch(request, *args, **kwargs)
        except ProtectedError as e:
            protected_objects = list(e.protected_objects)
            msg = f"unable to delete object. {len(protected_objects)} dependent objects were found: "
            msg += ", ".join([f"{obj} ({obj.pk})" for obj in protected_objects])
            logger.warning(msg)
            return self.finalize_response(
                request, Response({"detail": msg}, status=409), *args, **kwargs
            )
        except AbortRequest as e:
            logger.debug(e.message)
            return self.finalize_response(
                request, Response({"detail": e.message}, status=400), *args, **kwargs
            )

    # Creates

    def perform_create(self, serializer):
        model = self.queryset.model
        logger = logging.getLogger(
            f"peering_manager.api.views.{self.__class__.__name__}"
        )
        logger.info(f"creating new {model._meta.verbose_name}")

        # Enforce object-level permissions on save()
        try:
            with transaction.atomic():
                instance = serializer.save()
                self._validate_objects(instance)
        except ObjectDoesNotExist:
            raise PermissionDenied() from None

    # Updates

    def update(self, request, *args, **kwargs):
        # Hotwire get_object() to ensure we save a pre-change snapshot
        self.get_object = self.get_object_with_snapshot
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        model = self.queryset.model
        logger = logging.getLogger(
            f"peering_manager.api.views.{self.__class__.__name__}"
        )
        logger.info(
            f"updating {model._meta.verbose_name} {serializer.instance} (pk: {serializer.instance.pk})"
        )

        # Enforce object-level permissions on save()
        try:
            with transaction.atomic():
                instance = serializer.save()
                self._validate_objects(instance)
        except ObjectDoesNotExist:
            raise PermissionDenied() from None

    # Deletes

    def destroy(self, request, *args, **kwargs):
        # Hotwire get_object() to ensure we save a pre-change snapshot
        self.get_object = self.get_object_with_snapshot
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        model = self.queryset.model
        logger = logging.getLogger(
            f"peering_manager.api.views.{self.__class__.__name__}"
        )
        logger.info(
            f"deleting {model._meta.verbose_name} {instance} (pk: {instance.pk})"
        )

        return super().perform_destroy(instance)
