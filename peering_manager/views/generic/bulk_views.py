import logging

from django.contrib import messages
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import ManyToManyField, ProtectedError
from django.db.models.fields.reverse_related import ManyToManyRel
from django.forms import ModelMultipleChoiceField, MultipleHiddenInput
from django.forms.formsets import formset_factory
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.views.generic import View

from extras.signals import clear_webhooks
from peering_manager.forms import HiddenControlFormSet
from utils.exceptions import AbortRequest, PermissionsViolation
from utils.forms import ConfirmationForm
from utils.functions import get_permission_for_model, handle_protectederror
from utils.views import GetReturnURLMixin, PermissionRequiredMixin

from .base import BaseMultiObjectView
from .mixins import ActionsMixin, TableMixin
from .utils import get_prerequisite_model


class ObjectListView(BaseMultiObjectView, ActionsMixin, TableMixin):
    """
    Lists a series of objects.
    """

    template_name = "generic/object_list.html"
    filterset = None
    filterset_form = None

    def get_required_permission(self):
        return get_permission_for_model(self.queryset.model, "view")

    def get(self, request):
        model = self.queryset.model

        if self.filterset:
            self.queryset = self.filterset(
                request.GET, self.queryset, request=request
            ).qs

        # Determine the available actions
        actions = self.get_permitted_actions(request.user)
        has_bulk_actions = any(a.startswith("bulk_") for a in actions)

        # Render the objects table
        table = self.get_table(self.queryset, request, has_bulk_actions)

        context = {
            "model": model,
            "table": table,
            "actions": actions,
            "filterset_form": (
                self.filterset_form(request.GET, label_suffix="")
                if self.filterset_form
                else None
            ),
            "prerequisite_model": get_prerequisite_model(self.queryset),
            **self.get_extra_context(request),
        }

        return render(request, self.template_name, context)


class BulkEditView(GetReturnURLMixin, BaseMultiObjectView):
    """
    Edit objects in bulk.
    """

    template_name = "generic/bulk_edit.html"
    filterset = None
    form = None

    def get_required_permission(self):
        return get_permission_for_model(self.queryset.model, "change")

    def _update_objects(self, form, request):
        standard_fields = [field for field in form.fields if field != "pk"]
        nullified_fields = request.POST.getlist("_nullify")
        updated_objects = []
        model_fields = {}
        m2m_fields = {}

        # Build list of model fields and m2m fields for later iteration
        for name in standard_fields:
            try:
                model_field = self.queryset.model._meta.get_field(name)
                if isinstance(model_field, (ManyToManyField, ManyToManyRel)):
                    m2m_fields[name] = model_field
                else:
                    model_fields[name] = model_field
            except FieldDoesNotExist:
                # This form field is used to modify a field rather than set its value
                # directly
                model_fields[name] = None

        for o in self.queryset.filter(pk__in=form.cleaned_data["pk"]):
            # Take a snapshot of change-logged models
            if hasattr(o, "snapshot"):
                o.snapshot()

            # Update standard fields. If a field is listed in _nullify, delete its
            # value
            for name, model_field in model_fields.items():
                # Handle nullification
                if name in form.nullable_fields and name in nullified_fields:
                    setattr(o, name, None if model_field.null else "")
                # Normal fields
                elif name in form.changed_data:
                    setattr(o, name, form.cleaned_data[name])

            o.full_clean()
            o.save()
            updated_objects.append(o)

            # Handle M2M fields after save
            for name in m2m_fields:
                if name in form.nullable_fields and name in nullified_fields:
                    getattr(o, name).clear()
                else:
                    getattr(o, name).set(form.cleaned_data[name])

            # Add/remove tags
            if form.cleaned_data.get("add_tags", None):
                o.tags.add(*form.cleaned_data["add_tags"])
            if form.cleaned_data.get("remove_tags", None):
                o.tags.remove(*form.cleaned_data["remove_tags"])

        return updated_objects

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
            form = self.form(request.POST, initial=initial_data)

            if form.is_valid():
                logger.debug("form validation was successful")
                try:
                    with transaction.atomic():
                        updated_objects = self._update_objects(form, request)

                    if updated_objects:
                        count = len(updated_objects)
                        msg = f"Updated {count} {model._meta.verbose_name if count == 1 else model._meta.verbose_name_plural}"
                        logger.info(msg)
                        messages.success(self.request, msg)

                    return redirect(self.get_return_url(request))
                except ValidationError as e:
                    messages.error(self.request, ", ".join(e.messages))
                    clear_webhooks.send(sender=self)
                except (AbortRequest, PermissionsViolation) as e:
                    logger.debug(e.message)
                    form.add_error(None, e.message)
                    clear_webhooks.send(sender=self)
            else:
                logger.debug("form validation failed")
        else:
            form = self.form(initial=initial_data)

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
                "model": model,
                "form": form,
                "table": table,
                "return_url": self.get_return_url(request),
                **self.get_extra_context(request),
            },
        )


class BulkDeleteView(GetReturnURLMixin, BaseMultiObjectView):
    """
    Deletes objects in bulk.
    """

    template_name = "generic/bulk_delete.html"
    filterset = None
    table = None

    def get_permission_required(self):
        return (get_permission_for_model(self.queryset.model, "delete"),)

    def get_form(self):
        """
        Provide a standard bulk delete form.
        """

        class BulkDeleteForm(ConfirmationForm):
            pk = ModelMultipleChoiceField(
                queryset=self.queryset, widget=MultipleHiddenInput
            )

        return BulkDeleteForm

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
                except AbortRequest as e:
                    logger.debug(e.message)
                    messages.error(request, mark_safe(e.message))
                    return redirect(self.get_return_url(request))

                msg = f"Deleted {deleted_count} {model._meta.verbose_name if deleted_count == 1 else model._meta.verbose_name_plural}"
                logger.info(msg)
                messages.success(request, msg)
                return redirect(self.get_return_url(request))

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
                "model": model,
                "form": form,
                "table": table,
                "return_url": self.get_return_url(request),
                **self.get_extra_context(request),
            },
        )


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
            object_form_set = formset_factory(
                self.form_model, formset=HiddenControlFormSet, extra=0, can_delete=True
            )
        else:
            object_form_set = formset_factory(
                self.form_model, formset=self.custom_formset, extra=0, can_delete=True
            )

        # Get dependencies
        base_objects = self.get_base_objects(request.POST.getlist("pk"))
        if not base_objects:
            # We don't have base objects to handle, proceed as if we were in the next
            # step of the form (object creation)
            formset = object_form_set(data=request.POST)
        else:
            # Proceed base object and fill in the form
            processed_base_objects = [
                self.process_base_object(request, o) for o in base_objects
            ]
            formset = object_form_set(initial=self.sort_objects(processed_base_objects))

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
