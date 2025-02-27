from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django.views.generic import View

from utils.views import PermissionRequiredMixin

__all__ = ("BaseMultiObjectView", "BaseObjectView")


class BaseObjectView(PermissionRequiredMixin, View):
    """
    Base class for generic views which display or manipulate a single object.

    The `queryset` property is a Django `QuerySet` from which the object(s) will be
    fetched.

    The `template_name` property is the name of the HTML template file to render.
    """

    queryset = None
    template_name = None

    def dispatch(self, request, *args, **kwargs):
        self.queryset = self.get_queryset(request)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, request):
        """
        Return the base queryset for the view. By default, this returns
        `self.queryset.all()`.
        """
        if self.queryset is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not define a queryset. Set queryset on the class or override its get_queryset() method."
            )
        return self.queryset.all()

    def get_object(self, **kwargs):
        """
        Return the object being viewed or modified.

        The object is identified by an arbitrary set of keyword arguments gleaned from
        the URL, which are passed to `get_object_or_404()`. (Typically, only a primary
        key is needed.)

        If no matching object is found, return a 404 response.
        """
        return get_object_or_404(self.queryset, **kwargs)

    def get_extra_context(self, request, instance):
        """
        Return any additional context data to include when rendering the template.
        """
        return {}


class BaseMultiObjectView(PermissionRequiredMixin, View):
    """
    Base class for generic views which display or manipulate multiple objects.

    The `queryset` property is a Django `QuerySet` from which the object(s) will be
    fetched.

    The `table` property is a django-tables2 `Table` class used to render the objects
    list.

    The `template_name` property is the name of the HTML template file to render.
    """

    queryset = None
    table = None
    template_name = None

    def dispatch(self, request, *args, **kwargs):
        self.queryset = self.get_queryset(request)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, request):
        """
        Return the base queryset for the view. By default, this returns
        `self.queryset.all()`.
        """
        if self.queryset is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not define a queryset. Set queryset on the class or override its get_queryset() method."
            )
        return self.queryset.all()

    def get_extra_context(self, request):
        """
        Return any additional context data to include when rendering the template.
        """
        return {}
