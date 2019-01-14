import sys

from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import CharField, Form, MultipleHiddenInput
from django.forms.formsets import formset_factory
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME
from django.views.generic import View

from django_tables2 import RequestConfig

from .filters import ObjectChangeFilter
from .forms import (
    BootstrapMixin,
    ConfirmationForm,
    CSVDataField,
    FilterChoiceField,
    ObjectChangeFilterForm,
)
from .models import ObjectChange
from .paginators import EnhancedPaginator
from .tables import ObjectChangeTable


class AddOrEditView(View):
    model = None
    form = None
    return_url = None
    template = "utils/object_add_edit.html"

    def get_object(self, kwargs):
        if "asn" in kwargs:
            # Lookup object by ASN
            return get_object_or_404(self.model, asn=kwargs["asn"])

        if "slug" in kwargs:
            # Lookup object by slug
            return get_object_or_404(self.model, slug=kwargs["slug"])

        if "pk" in kwargs:
            # Lookup object by PK
            return get_object_or_404(self.model, pk=kwargs["pk"])

        # New object
        return self.model()

    def alter_object(self, obj, request, args, kwargs):
        return obj

    def get_return_url(self, obj):
        if obj.pk:
            # If the object has an absolute URL, use it
            return obj.get_absolute_url()

        if self.return_url:
            # Otherwise use the default URL if given
            return reverse(self.return_url)

        # Or return to home
        return reverse("home")

    def get(self, request, *args, **kwargs):
        """
        Method used to render the view when form is not submitted.
        """
        obj = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        form = self.form(instance=obj, initial=request.GET)

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )

    def post(self, request, *args, **kwargs):
        """
        The form has been submitted, process it.
        """
        obj = self.get_object(kwargs)
        form = self.form(request.POST, instance=obj)

        if form.is_valid():
            # Check if the object will be created or modified
            created = not form.instance.pk

            # Save the object
            obj = form.save()

            # Notify user with a message
            message = "Created " if created else "Modified "
            message = "{} {} {}".format(
                message, self.model._meta.verbose_name, escape(obj)
            )
            messages.success(request, mark_safe(message))

            # Redirect the user to the current page to create another object
            if "_addanother" in request.POST:
                return redirect(request.get_full_path())

            return redirect(self.get_return_url(obj))

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(obj),
            },
        )


class BulkAddFromDependencyView(View):
    model = None
    dependency_model = None
    custom_formset = None
    form_model = None
    return_url = None
    template = "utils/table_import.html"

    def get_dependency_objects(self, pk_list):
        # Returns the list of objects to be used as dependencies
        if not self.dependency_model:
            return []
        return list(self.dependency_model.objects.filter(pk__in=pk_list))

    def process_dependency_object(self, dependency):
        return None

    def sort_objects(self, object_list):
        return []

    def get_return_url(self):
        if self.return_url:
            # Use the default URL if given
            return self.return_url

        # Or return to home
        return reverse("home")

    def get(self, request):
        # Don't allow direct GET requests
        return redirect(self.get_return_url())

    def post(self, request):
        """
        The form has been submitted, process it.
        """
        # Determine URL to redirect users
        posted_return_url = request.POST.get("return_url")
        if posted_return_url and is_safe_url(
            url=posted_return_url, allowed_hosts=[request.get_host()]
        ):
            self.return_url = posted_return_url

        # Prepare the form
        if not self.custom_formset:
            ObjectFormSet = formset_factory(self.form_model, extra=0)
        else:
            ObjectFormSet = formset_factory(
                self.form_model, formset=self.custom_formset, extra=0
            )

        # Get dependencies
        dependencies = self.get_dependency_objects(request.POST.getlist("pk"))
        if not dependencies:
            # We don't have dependencies to handle, proceed as if we were in
            # the next step of the form (object addition)
            formset = ObjectFormSet(data=request.POST)
        else:
            # Proceed dependencies and fill in the form
            dependencies_processing_result = []
            for dependency in dependencies:
                dependencies_processing_result.append(
                    self.process_dependency_object(dependency)
                )

            formset = ObjectFormSet(
                initial=self.sort_objects(dependencies_processing_result)
            )

        new_objects = []
        if formset.is_valid():
            with transaction.atomic():
                for form in formset:
                    if form.is_valid():
                        instance = form.save()
                        new_objects.append(instance)

            if new_objects:
                # Notify user of successful import
                message = "Imported {} {}".format(
                    len(new_objects), new_objects[0]._meta.verbose_name_plural
                )
                messages.success(request, message)

            return redirect(self.get_return_url())

        return render(
            request,
            self.template,
            {
                "formset": formset,
                "obj_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.get_return_url(),
            },
        )


class BulkDeleteView(View):
    model = None
    queryset = None
    filter = None
    table = None
    template = "utils/object_bulk_delete.html"
    return_url = "home"

    def get(self, request):
        return redirect(self.return_url)

    def get_form(self):
        class BulkDeleteForm(ConfirmationForm):
            pk = FilterChoiceField(
                queryset=self.model.objects.all(), widget=MultipleHiddenInput
            )

        return BulkDeleteForm

    def filter_by_extra_context(self, queryset, request, kwargs):
        """
        This function provides a way to narrow a queryset based on the request
        and optional arguments. It must return a queryset as well.
        """
        return queryset

    def post(self, request, **kwargs):
        # Determine URL to redirect users
        posted_return_url = request.POST.get("return_url")
        if posted_return_url and is_safe_url(
            url=posted_return_url, allowed_hosts=[request.get_host()]
        ):
            self.return_url = posted_return_url

        # Build the list primary keys of the objects to delete
        if request.POST.get("_all") and self.filter is not None:
            pk_list = [
                obj.pk
                for obj in self.filter(
                    request.GET,
                    self.filter_by_extra_context(
                        self.model.objects.only("pk"), request, kwargs
                    ),
                ).qs
            ]
        else:
            pk_list = [int(pk) for pk in request.POST.getlist("pk")]

        form_model = self.get_form()
        if "_confirm" in request.POST:
            form = form_model(request.POST)
            if form.is_valid():
                queryset = self.model.objects.filter(pk__in=pk_list)

                try:
                    deleted_count = queryset.delete()[1][self.model._meta.label]
                except ProtectedError as e:
                    return redirect(self.return_url)

                message = "Deleted {} {}".format(
                    deleted_count, self.model._meta.verbose_name_plural
                )
                messages.success(request, message)

                return redirect(self.return_url)
        else:
            form = form_model(initial={"pk": pk_list, "return_url": self.return_url})

        # Retrieve objects being deleted
        queryset = self.queryset or self.model.objects.all()
        table = self.table(queryset.filter(pk__in=pk_list), orderable=False)
        if not table.rows:
            messages.warning(
                request,
                "No {} were selected for deletion.".format(
                    self.model._meta.verbose_name_plural
                ),
            )
            return redirect(self.return_url)

        return render(
            request,
            self.template,
            {
                "form": form,
                "object_type_plural": self.model._meta.verbose_name_plural,
                "table": table,
                "return_url": self.return_url,
            },
        )


class BulkEditView(View):
    queryset = None
    parent_model = None
    filter = None
    table = None
    form = None
    template = "utils/object_bulk_edit.html"
    return_url = None

    def get_return_url(self, request):
        if self.return_url:
            # Use the default URL if given
            return self.return_url

        if request.POST.get("return_url"):
            return request.POST.get("return_url")

        # Or return to home
        return reverse("home")

    def get(self, request):
        return redirect(self.get_return_url(request))

    def post(self, request, **kwargs):
        model = self.queryset.model

        # If we are working with a parent object, lets use it
        parent_object = (
            get_object_or_404(self.parent_model, **kwargs)
            if self.parent_model
            else None
        )

        # Check if the user asked for all objects to be edited
        if request.POST.get("_all") and self.filter:
            pk_list = [
                obj.pk for obj in self.filter(request.GET, model.objects.only("pk")).qs
            ]
        else:
            pk_list = [int(pk) for pk in request.POST.getlist("pk")]

        if "_apply" in request.POST:
            form = self.form(model, parent_object, request.POST)
            if form.is_valid():
                fields = [field for field in form.fields if field != "pk"]
                nullified_fields = request.POST.getlist("_nullify")

                try:
                    with transaction.atomic():
                        updated_count = 0
                        for obj in model.objects.filter(pk__in=pk_list):
                            for name in fields:
                                if (
                                    name in form.nullable_fields
                                    and name in nullified_fields
                                ):
                                    setattr(
                                        obj,
                                        name,
                                        ""
                                        if isinstance(form.fields[name], CharField)
                                        else None,
                                    )
                                elif form.cleaned_data[name] not in (None, ""):
                                    if isinstance(form.fields[name], FilterChoiceField):
                                        getattr(obj, name).set(form.cleaned_data[name])
                                    else:
                                        setattr(obj, name, form.cleaned_data[name])
                            obj.full_clean()
                            obj.save()
                            updated_count += 1

                    if updated_count:
                        message = "Updated {} {}".format(
                            updated_count, model._meta.verbose_name_plural
                        )
                        messages.success(self.request, message)

                    return redirect(self.get_return_url(request))
                except ValidationError as e:
                    messages.error(
                        self.request, "{} failed validation: {}".format(obj, e)
                    )
        else:
            initial_data = request.POST.copy()
            initial_data["pk"] = pk_list
            form = self.form(model, parent_object, initial=initial_data)

        # Retrieve objects being edited
        table = self.table(self.queryset.filter(pk__in=pk_list), orderable=False)
        if not table.rows:
            messages.warning(
                request, "No {} were selected.".format(model._meta.verbose_name_plural)
            )
            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template,
            {
                "form": form,
                "table": table,
                "object_type_plural": model._meta.verbose_name_plural,
                "return_url": self.get_return_url(request),
            },
        )


class ConfirmationView(View):
    return_url = None
    template = None

    def extra_context(self, kwargs):
        return {}

    def process(self, request, kwargs):
        pass

    def get(self, request, *args, **kwargs):
        form = ConfirmationForm(initial=request.GET)
        context = {"form": form}
        context.update(self.extra_context(kwargs))

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            return self.process(request, kwargs)

        context = {"form": form}
        context.update(self.extra_context(kwargs))

        return render(request, self.template, context)


class DeleteView(View):
    model = None
    return_url = None
    template = "utils/object_delete.html"

    def get_object(self, kwargs):
        if "asn" in kwargs:
            # Lookup object by ASN
            return get_object_or_404(self.model, asn=kwargs["asn"])

        if "slug" in kwargs:
            # Lookup object by slug
            return get_object_or_404(self.model, slug=kwargs["slug"])

        if "pk" in kwargs:
            # Lookup object by PK
            return get_object_or_404(self.model, pk=kwargs["pk"])

        return None

    def get_return_url(self, obj):
        if obj.pk:
            # If the object has an absolute URL, use it
            return obj.get_absolute_url()

        if self.return_url:
            # Otherwise use the default URL if given
            return reverse(self.return_url)

        # Or return to home
        return reverse("home")

    def get(self, request, *args, **kwargs):
        """
        Method used to render the view when form is not submitted.
        """
        obj = self.get_object(kwargs)
        form = ConfirmationForm(initial=request.GET)

        return render(
            request,
            self.template,
            {
                "object": obj,
                "form": form,
                "object_type": self.model._meta.verbose_name,
                "return_url": self.get_return_url(obj),
            },
        )

    def post(self, request, *args, **kwargs):
        """
        The form has been submitted, process it.
        """
        obj = self.get_object(kwargs)
        form = ConfirmationForm(request.POST)

        if form.is_valid():
            obj.delete()

            # Notify the user
            message = "Deleted {} {}".format(self.model._meta.verbose_name, escape(obj))
            messages.success(request, message)

            return redirect(self.get_return_url(obj))

        return render(
            request,
            self.template,
            {
                "object": obj,
                "form": form,
                "object_type": self.model._meta.verbose_name,
                "return_url": self.get_return_url(obj),
            },
        )


class ImportView(View):
    form_model = None
    return_url = None
    template = "utils/object_import.html"

    def import_form(self, *args, **kwargs):
        fields = self.form_model().fields.keys()

        class ImportForm(BootstrapMixin, Form):
            csv = CSVDataField(fields=fields)

        return ImportForm(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Method used to render the view when form is not submitted.
        """
        return render(
            request,
            self.template,
            {
                "form": self.import_form(),
                "fields": self.form_model().fields,
                "obj_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.return_url,
            },
        )

    def post(self, request, *args, **kwargs):
        """
        The form has been submitted, process it.
        """
        new_objects = []
        form = self.import_form(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    for row, data in enumerate(form.cleaned_data["csv"], start=1):
                        # Use a proper form for the given object/model
                        object_form = self.form_model(data)
                        if object_form.is_valid():
                            # Save the object
                            obj = object_form.save()
                            new_objects.append(obj)
                        else:
                            # Handle issues for each row
                            for field, err in object_form.errors.items():
                                form.add_error(
                                    "csv", "Row {} {}: {}".format(row, field, err[0])
                                )
                            raise ValidationError("")

                if new_objects:
                    # Notify user of successful import
                    message = "Imported {} {}".format(
                        len(new_objects), new_objects[0]._meta.verbose_name_plural
                    )
                    messages.success(request, message)

                    return redirect(self.return_url)
            except ValidationError:
                pass

        return render(
            request,
            self.template,
            {
                "form": form,
                "fields": self.form_model().fields,
                "object_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.return_url,
            },
        )


class ModelListView(View):
    queryset = None
    filter = None
    filter_form = None
    table = None
    template = None

    def build_queryset(self, request, kwargs):
        return self.queryset

    def alter_queryset(self, request):
        return self.queryset.all()

    def extra_context(self, kwargs):
        return {}

    def setup_table_columns(self, request, permissions, table, kwargs):
        if "pk" in table.base_columns and (
            permissions["add"] or permissions["change"] or permissions["delete"]
        ):
            table.columns.show("pk")

    def get(self, request, *args, **kwargs):
        # If no query set has been provided for some reasons
        if not self.queryset:
            self.queryset = self.build_queryset(request, kwargs)

        # If there is a filter, apply it
        if self.filter:
            self.queryset = self.filter(request.GET, self.queryset).qs

        # Alter the queryset if needed
        self.queryset = self.alter_queryset(request)

        # Compile user model permissions for access from within the template
        permission_name = "{}.{{}}_{}".format(
            self.queryset.model._meta.app_label, self.queryset.model._meta.model_name
        )
        permissions = {
            p: request.user.has_perm(permission_name.format(p))
            for p in ["add", "change", "delete"]
        }

        # Build the table based on the queryset
        table = self.table(self.queryset)
        self.setup_table_columns(request, permissions, table, kwargs)

        # Apply pagination
        paginate = {
            "paginator_class": EnhancedPaginator,
            "per_page": request.GET.get("per_page", settings.PAGINATE_COUNT),
        }
        RequestConfig(request, paginate).configure(table)

        # Set context and render
        context = {
            "table": table,
            "filter": self.filter,
            "filter_form": self.filter_form(request.GET, label_suffix="")
            if self.filter_form
            else None,
            "permissions": permissions,
        }
        context.update(self.extra_context(kwargs))

        return render(request, self.template, context)


class TableImportView(View):
    custom_formset = None
    form_model = None
    return_url = None
    template = "utils/table_import.html"

    def get_objects(self):
        return []

    def get_return_url(self):
        if self.return_url:
            # Use the default URL if given
            return reverse(self.return_url)

        # Or return to home
        return reverse("home")

    def get(self, request):
        """
        Method used to render the view when form is not submitted.
        """
        objects = self.get_objects()
        formset = None

        if len(objects) > 0:
            if not self.custom_formset:
                ObjectFormSet = formset_factory(self.form_model, extra=0)
            else:
                ObjectFormSet = formset_factory(
                    self.form_model, formset=self.custom_formset, extra=0
                )
            formset = ObjectFormSet(initial=objects)
        else:
            messages.info(request, "No data to import.")
            return redirect(self.get_return_url())

        return render(
            request,
            self.template,
            {
                "formset": formset,
                "obj_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.get_return_url(),
            },
        )

    def post(self, request):
        """
        The form has been submitted, process it.
        """
        if not self.custom_formset:
            ObjectFormSet = formset_factory(self.form_model, extra=0)
        else:
            ObjectFormSet = formset_factory(
                self.form_model, formset=self.custom_formset, extra=0
            )
        formset = ObjectFormSet(request.POST)
        new_objects = []

        if formset.is_valid():
            with transaction.atomic():
                for form in formset:
                    if form.is_valid():
                        instance = form.save()
                        new_objects.append(instance)

            if new_objects:
                # Notify user of successful import
                message = "Imported {} {}".format(
                    len(new_objects), new_objects[0]._meta.verbose_name_plural
                )
                messages.success(request, message)

            return redirect(self.get_return_url())

        return render(
            request,
            self.template,
            {
                "formset": formset,
                "obj_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.get_return_url(),
            },
        )


class ObjectChangeList(ModelListView):
    queryset = ObjectChange.objects.select_related("user", "changed_object_type")
    filter = ObjectChangeFilter
    filter_form = ObjectChangeFilterForm
    table = ObjectChangeTable
    template = "utils/object_change/list.html"


class ObjectChangeDetails(View):
    def get(self, request, pk):
        object_change = get_object_or_404(ObjectChange, pk=pk)

        related_changes = ObjectChange.objects.filter(
            request_id=object_change.request_id
        ).exclude(pk=object_change.pk)
        related_changes_table = ObjectChangeTable(
            data=related_changes[:50], orderable=False
        )

        return render(
            request,
            "utils/object_change/details.html",
            {
                "object_change": object_change,
                "related_changes_table": related_changes_table,
                "related_changes_count": related_changes.count(),
            },
        )


@requires_csrf_token
def ServerError(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    Custom 500 handler to provide details when rendering 500.html.
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError(
            "<h1>Server Error (500)</h1>", content_type="text/html"
        )
    type_, error, _ = sys.exc_info()

    return HttpResponseServerError(
        template.render({"exception": str(type_), "error": error})
    )
