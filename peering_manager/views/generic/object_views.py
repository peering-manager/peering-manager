from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.html import escape
from django.utils.safestring import mark_safe

from extras.signals import clear_webhooks
from utils.exceptions import AbortRequestError, PermissionsViolationError
from utils.forms import ConfirmationForm
from utils.functions import get_permission_for_model, normalize_querydict
from utils.views import GetReturnURLMixin

from .base import BaseObjectView
from .mixins import ActionsMixin, TableMixin
from .utils import get_prerequisite_model

if TYPE_CHECKING:
    from utils.views import ViewTab


class ObjectView(BaseObjectView):
    """
    Retrieves a single object for display.
    """

    tab: ViewTab | None = None

    def get_required_permission(self):
        return get_permission_for_model(self.queryset.model, "view")

    def get_template_name(self):
        """
        Returns self.template_name if set. Otherwise, resolves the template path by
        model app_label and name.
        """
        if self.template_name:
            return self.template_name

        model_opts = self.queryset.model._meta
        return f"{model_opts.app_label}/{model_opts.model_name}/view.html"

    def get(self, request, *args, **kwargs):
        """
        Generic GET handler for accessing an object.
        """
        instance = self.get_object(**kwargs)

        return render(
            request,
            self.get_template_name(),
            {
                "instance": instance,
                "tab": self.tab,
                **self.get_extra_context(request, instance),
            },
        )


class ObjectChildrenView(ObjectView, ActionsMixin, TableMixin):
    """
    Displays a table of child objects associated with the parent object.
    """

    child_model = None
    table = None
    filterset = None
    filterset_form = None

    def get_children(self, request, parent):
        """
        Returns a `QuerySet` of child objects.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_children()"
        )

    def prep_table_data(self, request, queryset, parent):
        """
        Provides a hook for subclassed views to modify data before initializing the
        table.
        """
        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET handler for rendering child objects.
        """
        instance = self.get_object(**kwargs)
        child_objects = self.get_children(request, instance)

        if self.filterset:
            child_objects = self.filterset(request.GET, child_objects).qs
        if self.filterset_form:
            filterset_form = self.filterset_form(request.GET, label_suffix="")
        else:
            filterset_form = None

        # Determine the available actions
        actions = self.get_permitted_actions(request.user, model=self.child_model)
        has_bulk_actions = any(a.startswith("bulk_") for a in actions)

        table_data = self.prep_table_data(request, child_objects, instance)
        table = self.get_table(table_data, request, has_bulk_actions)

        return render(
            request,
            self.get_template_name(),
            {
                "instance": instance,
                "child_model": self.child_model,
                "table": table,
                "actions": actions,
                "tab": self.tab,
                "filterset_form": filterset_form,
                **self.get_extra_context(request, instance),
            },
        )


class ObjectEditView(GetReturnURLMixin, BaseObjectView):
    """
    Create or edit a single object.

    The `form` property corresponds to the form used to create or edit the object.
    """

    template_name = "generic/edit.html"
    form = None

    def dispatch(self, request, *args, **kwargs):
        # Determine required permission based on whether we are editing an existing
        # object
        self._permission_action = "change" if kwargs else "add"

        return super().dispatch(request, *args, **kwargs)

    def get_permission_required(self):
        # self._permission_action is set by dispatch() to either "add" or "change"
        # depending on whether we are modifying an existing object or creating a new one.
        return (get_permission_for_model(self.queryset.model, self._permission_action),)

    def get_object(self, **kwargs):
        """
        Return an object for editing.

        If no keyword arguments have been specified, this will be a new instance.
        """
        if not kwargs:
            return self.queryset.model()
        return super().get_object(**kwargs)

    def alter_object(self, instance, request, url_args, url_kwargs):
        """
        Provides a hook for views to modify an object before it is processed.

        For example, a parent object can be defined given some parameter from the
        request URL.
        """
        return instance

    def get_extra_addanother_params(self, request):
        """
        Return a dictionary of extra parameters to use on the "Add Another" button.
        """
        return {}

    def get(self, request, *args, **kwargs):
        instance = self.get_object(**kwargs)
        instance = self.alter_object(instance, request, args, kwargs)
        model = self.queryset.model

        initial_data = normalize_querydict(request.GET)
        form = self.form(instance=instance, initial=initial_data)

        return render(
            request,
            self.template_name,
            {
                "model": model,
                "instance": instance,
                "form": form,
                "return_url": self.get_return_url(request, instance),
                "prerequisite_model": get_prerequisite_model(self.queryset),
                **self.get_extra_context(request, instance),
            },
        )

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger("peering.manager.views.ObjectEditView")
        instance = self.get_object(**kwargs)

        # Take a snapshot for change logging (if editing an existing object)
        if instance.pk and hasattr(instance, "snapshot"):
            instance.snapshot()

        instance = self.alter_object(instance, request, args, kwargs)

        form = self.form(data=request.POST, files=request.FILES, instance=instance)
        if form.is_valid():
            logger.debug("Form validation was successful")

            try:
                with transaction.atomic():
                    object_created = form.instance.pk is None
                    instance = form.save()

                    # Check that the new object conforms with any permissions
                    if not self.queryset.filter(pk=instance.pk).exists():
                        raise PermissionsViolationError()

                msg = "{} {}".format(
                    "Created" if object_created else "Modified",
                    self.queryset.model._meta.verbose_name,
                )
                logger.info(f"{msg} {instance} (PK: {instance.pk})")
                if hasattr(instance, "get_absolute_url"):
                    msg = mark_safe(
                        f'{msg} <a href="{instance.get_absolute_url()}">{escape(instance)}</a>'
                    )
                else:
                    msg = f"{msg} {instance}"
                messages.success(request, msg)

                if "_addanother" in request.POST:
                    return redirect(request.path)
                return redirect(self.get_return_url(request, instance))
            except (AbortRequestError, PermissionsViolationError) as e:
                logger.debug(e.message)
                form.add_error(None, e.message)
                clear_webhooks.send(sender=self)
        else:
            logger.debug("Form validation failed")

        return render(
            request,
            self.template_name,
            {
                "instance": instance,
                "form": form,
                "return_url": self.get_return_url(request, instance),
                **self.get_extra_context(request, instance),
            },
        )


class ObjectDeleteView(GetReturnURLMixin, BaseObjectView):
    """
    Deletes a single object.
    """

    template_name = "generic/object_delete.html"

    def get(self, request, **kwargs):
        o = self.get_object(**kwargs)
        form = ConfirmationForm(initial=request.GET)

        return render(
            request,
            self.template_name,
            {
                "object": o,
                "object_type": self.queryset.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(request, instance=o),
            },
        )

    def post(self, request, **kwargs):
        logger = logging.getLogger("peering.manager.views.ObjectDeleteView")
        o = self.get_object(**kwargs)
        form = ConfirmationForm(request.POST)

        # Take a snapshot of change-logged models
        if hasattr(o, "snapshot"):
            o.snapshot()

        if form.is_valid():
            logger.debug("form validation was successful")
            o.delete()

            msg = f"Deleted {self.queryset.model._meta.verbose_name} {o}"
            logger.info(msg)
            messages.success(request, msg)

            return_url = form.cleaned_data.get("return_url")
            if return_url and return_url.startswith("/"):
                return redirect(return_url)
            return redirect(self.get_return_url(request, instance=o))

        logger.debug("form validation failed")
        return render(
            request,
            self.template_name,
            {
                "object": o,
                "object_type": self.queryset.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(request, instance=o),
            },
        )
