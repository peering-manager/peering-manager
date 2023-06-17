import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as _PermissionRequiredMixin,
)
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import ManyToManyField, ProtectedError
from django.forms import ModelMultipleChoiceField, MultipleHiddenInput
from django.forms.formsets import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views.generic import View

from extras.signals import clear_webhooks
from peering_manager.forms import HiddenControlFormSet
from utils.forms import ConfirmationForm, TableConfigurationForm
from utils.functions import (
    get_permission_for_model,
    handle_protectederror,
    normalize_querydict,
)
from utils.tables import paginate_table


class PermissionRequiredMixin(_PermissionRequiredMixin):
    """
    Overrides the original `PermissionRequiredMixin` class to handle the
    `LOGIN_REQUIRED` with `*.view_*` permission.
    """

    def has_permission(self):
        if (
            not settings.LOGIN_REQUIRED
            and isinstance(self.permission_required, str)
            and ".view_" in self.permission_required
        ):
            return True
        else:
            return super().has_permission()


class GetReturnURLMixin(object):
    """
    Provides logic for determining where a user should be redirected
    after processing a form.
    """

    default_return_url = None

    def get_return_url(self, request, instance=None):
        # Check if `return_url` was specified as a query parameter or form
        # data, use this URL only if it's safe
        return_url = request.GET.get("return_url") or request.POST.get("return_url")
        if return_url and return_url.startswith("/"):
            return return_url

        # Check if the object being modified (if any) has an absolute URL
        if (
            instance is not None
            and instance.pk
            and hasattr(instance, "get_absolute_url")
        ):
            return instance.get_absolute_url()

        # Fall back to the default URL (if specified) for the view
        if self.default_return_url is not None:
            return reverse(self.default_return_url)

        # Try to resolve the list view for the object
        if hasattr(self, "queryset"):
            model_opts = self.queryset.model._meta
            try:
                return reverse(f"{model_opts.app_label}:{model_opts.model_name}_list")
            except NoReverseMatch:
                pass

        # If all fails, send the user to the homepage
        return reverse("home")


class TableConfigurationMixin(object):
    """
    Provides default functions implementation to handle table configuration
    form.
    """

    def table_configuration_form(self, table):
        return TableConfigurationForm(table=table)

    def post(self, request, **kwargs):
        table = self.table(self.queryset)
        form = TableConfigurationForm(table=table, data=request.POST)

        if form.is_valid():
            preference = f"tables.{self.table.__name__}.columns".lower()

            if "save" in request.POST:
                request.user.preferences.set(
                    preference, form.cleaned_data["columns"], commit=True
                )
            elif "reset" in request.POST:
                request.user.preferences.delete(preference, commit=True)
            messages.success(request, "Your preferences have been updated.")

        return redirect(request.get_full_path())


class ObjectView(PermissionRequiredMixin, View):
    """
    Retrieves a single object for display.
    """

    queryset = None
    template_name = None

    def get_template_name(self):
        """
        Returns self.template_name if set. Otherwise, resolves the template path by
        model app_label and name.
        """
        if self.template_name:
            return self.template_name

        model_opts = self.queryset.model._meta
        return f"{model_opts.app_label}/{model_opts.model_name}/view.html"

    def get_extra_context(self, request, instance):
        """
        Returns any additional context data for the template.
        """
        return {}

    def get(self, request, *args, **kwargs):
        """
        Generic GET handler for accessing an object.
        """
        instance = get_object_or_404(self.queryset, **kwargs)

        return render(
            request,
            self.get_template_name(),
            {
                "instance": instance,
                **self.get_extra_context(request, instance),
            },
        )


class ObjectChildrenView(TableConfigurationMixin, ObjectView):
    """
    Displays a table of child objects associated with the parent object.
    """

    queryset = None
    child_model = None
    table = None
    filterset = None
    filterset_form = None
    template_name = None

    def get_children(self, request, parent):
        """
        Returns a `QuerySet` of child objects.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_children()"
        )

    def prepare_table_data(self, request, queryset, parent):
        """
        Provides a hook for subclassed views to modify data before initializing the
        table.
        """
        return queryset

    def get(self, request, *args, **kwargs):
        """
        GET handler for rendering child objects.
        """
        instance = get_object_or_404(self.queryset, **kwargs)
        child_objects = self.get_children(request, instance)

        if self.filterset:
            child_objects = self.filterset(request.GET, child_objects).qs

        permissions = {}
        for action in ("add", "change", "delete"):
            perm_name = get_permission_for_model(self.child_model, action)
            permissions[action] = request.user.has_perm(perm_name)

        table = self.table(
            self.prepare_table_data(request, child_objects, instance), user=request.user
        )
        # Determine whether to display bulk action checkboxes
        if "pk" in table.base_columns and (
            permissions["change"] or permissions["delete"]
        ):
            table.columns.show("pk")
        paginate_table(table, request)

        return render(
            request,
            self.get_template_name(),
            {
                "instance": instance,
                "table": table,
                "table_configuration_form": self.table_configuration_form(table),
                "permissions": permissions,
                "filter_form": self.filterset_form(request.GET, label_suffix="")
                if self.filterset_form
                else None,
                **self.get_extra_context(request, instance),
            },
        )


class ObjectListView(PermissionRequiredMixin, TableConfigurationMixin, View):
    """
    Lists a series of objects.
    """

    queryset = None
    filterset = None
    filterset_form = None
    table = None
    template_name = "generic/object_list.html"

    def extra_context(self):
        return {}

    def alter_queryset(self):
        """
        Provides a hook to change the queryset before building the table.
        """
        pass

    def get_table(self, request, permissions):
        table = self.table(self.queryset, user=request.user)
        if "pk" in table.base_columns and (
            permissions["change"] or permissions["delete"]
        ):
            table.columns.show("pk")

        return table

    def get(self, request):
        model = self.queryset.model
        content_type = ContentType.objects.get_for_model(model)

        self.alter_queryset()
        if self.filterset:
            self.queryset = self.filterset(request.GET, self.queryset).qs

        # Compile a dictionary indicating which permissions are available to the current user for this model
        permissions = {}
        for action in ("add", "change", "delete", "view"):
            perm_name = get_permission_for_model(model, action)
            permissions[action] = request.user.has_perm(perm_name)

        # Render the objects table
        table = self.get_table(request, permissions)
        paginate_table(table, request)

        context = {
            "content_type": content_type,
            "table": table,
            "table_configuration_form": self.table_configuration_form(table),
            "permissions": permissions,
            "filter_form": self.filterset_form(request.GET, label_suffix="")
            if self.filterset_form
            else None,
        }
        context.update(self.extra_context())

        return render(request, self.template_name, context)


class ObjectEditView(GetReturnURLMixin, PermissionRequiredMixin, View):
    """
    Creates or edit a single object.
    """

    queryset = None
    model_form = None
    template_name = "generic/object_edit.html"

    def get_object(self, kwargs):
        if "pk" in kwargs:
            o = get_object_or_404(self.queryset, pk=kwargs["pk"])
        else:
            return self.queryset.model()

        # Take a snapshot of change-logged models
        if hasattr(o, "snapshot"):
            o.snapshot()

        return o

    def alter_object(self, instance, request, url_args, url_kwargs):
        """
        Allows views to add extra info to an object before it is processed.

        For example, a parent object can be defined given some parameter from
        the request URL.
        """
        return instance

    def dispatch(self, request, *args, **kwargs):
        # Determine required permission based on whether we are editing an existing object
        self._permission_action = "change" if kwargs else "add"

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        o = self.alter_object(self.get_object(kwargs), request, args, kwargs)

        initial_data = normalize_querydict(request.GET)
        form = self.model_form(instance=o, initial=initial_data)

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

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger("peering.manager.views.ObjectEditView")
        o = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        form = self.model_form(data=request.POST, files=request.FILES, instance=o)

        if form.is_valid():
            logger.debug("form validation was successful")

            with transaction.atomic():
                object_created = form.instance.pk is None
                o = form.save()

            msg = f"{'Created' if object_created else 'Modified'} {self.queryset.model._meta.verbose_name}"
            logger.info(f"{msg} {o} (pk: {o.pk})")
            if hasattr(o, "get_absolute_url"):
                msg = f'{msg} <a href="{o.get_absolute_url()}">{escape(o)}</a>'
            else:
                msg = f"{msg} {escape(o)}"
            messages.success(request, mark_safe(msg))

            if "_addanother" in request.POST:
                redirect_url = request.path
                if "return_url" in request.GET:
                    redirect_url += f"?return_url={request.GET.get('return_url')}"
                return redirect(redirect_url)

            return redirect(self.get_return_url(request, instance=o))
        else:
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


class ObjectDeleteView(GetReturnURLMixin, PermissionRequiredMixin, View):
    """
    Deletes a single object.
    """

    queryset = None
    template_name = "generic/object_delete.html"

    def get_object(self, kwargs):
        o = get_object_or_404(self.queryset, pk=kwargs["pk"])

        # Take a snapshot of change-logged models
        if hasattr(o, "snapshot"):
            o.snapshot()

        return o

    def get(self, request, **kwargs):
        o = self.get_object(kwargs)
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
        o = self.get_object(kwargs)
        form = ConfirmationForm(request.POST)

        if form.is_valid():
            logger.debug("form validation was successful")
            o.delete()

            msg = f"Deleted {self.queryset.model._meta.verbose_name} {o}"
            logger.info(msg)
            messages.success(request, msg)

            return_url = form.cleaned_data.get("return_url")
            if return_url and return_url.startswith("/"):
                return redirect(return_url)
            else:
                return redirect(self.get_return_url(request, instance=o))
        else:
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


class BulkEditView(GetReturnURLMixin, PermissionRequiredMixin, View):
    """
    Edits objects in bulk.
    """

    queryset = None
    filterset = None
    table = None
    form = None
    template_name = "generic/object_bulk_edit.html"

    def get(self, request):
        return redirect(self.get_return_url(request))

    def post(self, request, **kwargs):
        logger = logging.getLogger("peering.manager.views.BulkEditView")
        model = self.queryset.model

        # If we are editing *all* objects in the queryset, replace the PK list with
        # all matched objects
        if request.POST.get("_all") and self.filterset is not None:
            pk_list = self.filterset(
                request.GET, self.queryset.values_list("pk", flat=True)
            ).qs
        else:
            pk_list = request.POST.getlist("pk")

        # Include the PK list as initial data for the form
        initial_data = {"pk": pk_list}

        if "_apply" in request.POST:
            form = self.form(model, request.POST, initial=initial_data)

            if form.is_valid():
                logger.debug("form validation was successful")
                fields = [field for field in form.fields if field != "pk"]
                nullified_fields = request.POST.getlist("_nullify")

                try:
                    with transaction.atomic():
                        updated_objects = []
                        for o in self.queryset.filter(pk__in=form.cleaned_data["pk"]):
                            # Take a snapshot of change-logged models
                            if hasattr(o, "snapshot"):
                                o.snapshot()

                            # Update standard fields. If a field is listed in _nullify
                            # delete its value
                            for name in fields:
                                try:
                                    model_field = model._meta.get_field(name)
                                except FieldDoesNotExist:
                                    # This form field is used to modify a field rather
                                    # than set its value directly
                                    model_field = None

                                # Handle nullification
                                if (
                                    name in form.nullable_fields
                                    and name in nullified_fields
                                ):
                                    if isinstance(model_field, ManyToManyField):
                                        getattr(o, name).set([])
                                    else:
                                        setattr(
                                            o, name, None if model_field.null else ""
                                        )
                                # ManyToManyFields
                                elif isinstance(model_field, ManyToManyField):
                                    if form.cleaned_data[name]:
                                        getattr(o, name).set(form.cleaned_data[name])
                                # Normal fields
                                elif name in form.changed_data:
                                    setattr(o, name, form.cleaned_data[name])

                            o.full_clean()
                            o.save()
                            updated_objects.append(o)
                            logger.debug(f"saved {o} (pk: {o.pk})")

                            # Add/remove tags
                            if form.cleaned_data.get("add_tags", None):
                                o.tags.add(*form.cleaned_data["add_tags"])
                            if form.cleaned_data.get("remove_tags", None):
                                o.tags.remove(*form.cleaned_data["remove_tags"])

                    if updated_objects:
                        count = len(updated_objects)
                        msg = f"Updated {count} {model._meta.verbose_name if count == 1 else model._meta.verbose_name_plural}"
                        logger.info(msg)
                        messages.success(self.request, msg)

                    return redirect(self.get_return_url(request))
                except ValidationError as e:
                    messages.error(
                        self.request, f"{o} failed validation: {', '.join(e.messages)}"
                    )
                    clear_webhooks.send(sender=self)
            else:
                logger.debug("form validation failed")
        else:
            form = self.form(model, initial=initial_data)

        # Retrieve objects being edited
        table = self.table(self.queryset.filter(pk__in=pk_list), orderable=False)
        if "actions" in table.base_columns:
            table.columns.hide("actions")
        if not table.rows:
            messages.warning(
                request, f"No {model._meta.verbose_name_plural} were selected."
            )
            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "table": table,
                "object_type_plural": model._meta.verbose_name_plural,
                "return_url": self.get_return_url(request),
            },
        )


class BulkDeleteView(GetReturnURLMixin, PermissionRequiredMixin, View):
    """
    Deletes objects in bulk.
    """

    queryset = None
    filterset = None
    table = None
    form = None
    template_name = "generic/object_bulk_delete.html"

    def get(self, request):
        return redirect(self.get_return_url(request))

    def post(self, request, **kwargs):
        logger = logging.getLogger("peering.manager.views.BulkDeleteView")
        model = self.queryset.model

        # Are we deleting *all* objects in the queryset or just a selected subset?
        if request.POST.get("_all"):
            qs = model.objects.all()
            if self.filterset is not None:
                qs = self.filterset(request.GET, qs).qs
            pk_list = qs.only("pk").values_list("pk", flat=True)
        else:
            pk_list = [int(pk) for pk in request.POST.getlist("pk")]

        form_cls = self.get_form()

        if "_confirm" in request.POST:
            form = form_cls(request.POST)
            if form.is_valid():
                logger.debug("form validation was successful")

                # Delete objects
                queryset = self.queryset.filter(pk__in=pk_list)
                deleted_count = queryset.count()
                try:
                    for obj in queryset:
                        # Take a snapshot of change-logged models
                        if hasattr(obj, "snapshot"):
                            obj.snapshot()
                        obj.delete()
                except ProtectedError as e:
                    logger.info(
                        "caught ProtectedError while attempting to delete objects"
                    )
                    handle_protectederror(queryset, request, e)
                    return redirect(self.get_return_url(request))

                msg = f"Deleted {deleted_count} {model._meta.verbose_name if deleted_count == 1 else model._meta.verbose_name_plural}"
                logger.info(msg)
                messages.success(request, msg)
                return redirect(self.get_return_url(request))
            else:
                logger.debug("form validation failed")
        else:
            form = form_cls(
                initial={"pk": pk_list, "return_url": self.get_return_url(request)}
            )

        # Retrieve objects being deleted
        table = self.table(self.queryset.filter(pk__in=pk_list), orderable=False)
        if "actions" in table.base_columns:
            table.columns.hide("actions")
        if not table.rows:
            messages.warning(
                request,
                f"No {model._meta.verbose_name_plural} were selected for deletion.",
            )
            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object_type_plural": model._meta.verbose_name_plural,
                "table": table,
                "return_url": self.get_return_url(request),
            },
        )

    def get_form(self):
        """
        Provides a standard bulk delete form if none has been specified for the view
        """

        class BulkDeleteForm(ConfirmationForm):
            pk = ModelMultipleChoiceField(
                queryset=self.queryset, widget=MultipleHiddenInput
            )

        if self.form:
            return self.form

        return BulkDeleteForm


class ImportFromObjectView(GetReturnURLMixin, PermissionRequiredMixin, View):
    queryset = None
    custom_formset = None
    form_model = None
    template_name = "generic/object_import_from_base.html"

    def get_base_objects(self, pk_list):
        """
        Returns the list of objects to be used as dependencies.
        """
        if not self.queryset:
            return []
        else:
            return list(self.queryset.filter(pk__in=pk_list))

    def process_base_object(self, request, base):
        return None

    def sort_objects(self, object_list):
        return []

    def get(self, request):
        # Don't allow direct GET requests
        return redirect(self.get_return_url(request))

    def post(self, request):
        """
        The form has been submitted, process it.
        """
        logger = logging.getLogger("peering.manager.views.ImportFromObjectView")

        if "_add" in request.POST and not request.POST.getlist("pk"):
            messages.error(request, "No objects selected.")
            return redirect(self.get_return_url(request))

        # Prepare the form
        if not self.custom_formset:
            ObjectFormSet = formset_factory(
                self.form_model, formset=HiddenControlFormSet, extra=0, can_delete=True
            )
        else:
            ObjectFormSet = formset_factory(
                self.form_model, formset=self.custom_formset, extra=0, can_delete=True
            )

        # Get dependencies
        base_objects = self.get_base_objects(request.POST.getlist("pk"))
        if not base_objects:
            # We don't have base objects to handle, proceed as if we were in the next
            # step of the form (object creation)
            formset = ObjectFormSet(data=request.POST)
        else:
            # Proceed base object and fill in the form
            processed_base_objects = [
                self.process_base_object(request, o) for o in base_objects
            ]
            formset = ObjectFormSet(initial=self.sort_objects(processed_base_objects))

        created_objects = []
        if formset.is_valid():
            logger.debug("formset validation was successful")

            with transaction.atomic():
                for form in formset:
                    if formset.can_delete and formset._should_delete_form(form):
                        continue
                    if form.is_valid():
                        instance = form.save()
                        created_objects.append(instance)

            if created_objects:
                count = len(created_objects)
                msg = f"Imported {count} {created_objects[0]._meta.verbose_name if count == 1 else created_objects[0]._meta.verbose_name_plural}"
                logger.info(msg)
                messages.success(request, msg)

            return redirect(self.get_return_url(request))
        else:
            logger.debug("formset validation failed")

        return render(
            request,
            self.template_name,
            {
                "formset": formset,
                "object_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.get_return_url(request),
            },
        )
