import sys

from django.db import transaction
from django.db.models import Count, ManyToManyField, ProtectedError
from django.db.models.query import QuerySet
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as _PermissionRequiredMixin,
)
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.forms import CharField, MultipleHiddenInput
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

from .filters import ObjectChangeFilterSet, TagFilterSet
from .forms import (
    ConfirmationForm,
    DynamicModelMultipleChoiceField,
    ObjectChangeFilterForm,
    TableConfigurationForm,
    TagBulkEditForm,
    TagFilterForm,
    TagForm,
)
from .models import ObjectChange, Tag, TaggedItem
from .paginators import EnhancedPaginator, get_paginate_count
from .tables import ObjectChangeTable, TagTable


class PermissionRequiredMixin(_PermissionRequiredMixin):
    """
    Override the original `PermissionRequiredMixin` class to handle the
    `LOGIN_REQUIRED` with `*.view_*` permission.
    """

    def has_permission(self):
        if (
            not settings.LOGIN_REQUIRED
            and isinstance(self.permission_required, str)
            and ".view_" in self.permission_required
        ):
            return True
        return super().has_permission()


class ReturnURLMixin(object):
    """
    Provides a way to determine where a user should be redirected after processing a
    form.
    """

    default_return_url = None

    def get_return_url(self, request, obj=None):
        # First, see if `return_url` was specified as a query parameter or form data.
        # Use this URL only if it's considered safe.
        query_param = request.GET.get("return_url") or request.POST.get("return_url")
        if query_param and is_safe_url(
            url=query_param, allowed_hosts=request.get_host()
        ):
            return query_param
        # Next, check if the object being modified (if any) has an absolute URL.
        elif obj is not None and obj.pk and hasattr(obj, "get_absolute_url"):
            return obj.get_absolute_url()
        # Fall back to the default URL (if specified) for the view.
        elif self.default_return_url is not None:
            return reverse(self.default_return_url)
        # If all else fails, return home. Ideally this should never happen.
        return reverse("home")


class AddOrEditView(ReturnURLMixin, View):
    model = None
    form = None
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

    def get(self, request, *args, **kwargs):
        """
        Method used to render the view when form is not submitted.
        """
        obj = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        # Parse initial data manually to avoid setting field values as lists
        initial_data = {k: request.GET[k] for k in request.GET}
        form = self.form(instance=obj, initial=initial_data)

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(request, obj),
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

            return redirect(self.get_return_url(request, obj))

        return render(
            request,
            self.template,
            {
                "object": obj,
                "object_type": self.model._meta.verbose_name,
                "form": form,
                "return_url": self.get_return_url(request, obj),
            },
        )


class BulkAddFromDependencyView(ReturnURLMixin, View):
    model = None
    dependency_model = None
    custom_formset = None
    form_model = None
    template = "utils/table_import.html"

    def get_dependency_objects(self, pk_list):
        # Returns the list of objects to be used as dependencies
        if not self.dependency_model:
            return []
        return list(self.dependency_model.objects.filter(pk__in=pk_list))

    def process_dependency_object(self, request, dependency):
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
                    self.process_dependency_object(request, dependency)
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

            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template,
            {
                "formset": formset,
                "obj_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.get_return_url(request),
            },
        )


class BulkDeleteView(View):
    model = None
    queryset = None
    filter = None
    table = None
    template = "utils/object_bulk_delete.html"
    return_url = "home"
    hidden_columns = []

    def get(self, request):
        return redirect(self.return_url)

    def get_form(self):
        class BulkDeleteForm(ConfirmationForm):
            pk = DynamicModelMultipleChoiceField(
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
        if "actions" in table.base_columns:
            table.columns.hide("actions")
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


class BulkEditView(ReturnURLMixin, View):
    queryset = None
    parent_model = None
    filter = None
    table = None
    form = None
    template = "utils/object_bulk_edit.html"

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
                                try:
                                    model_field = model._meta.get_field(name)
                                except FieldDoesNotExist:
                                    pass

                                if (
                                    name in form.nullable_fields
                                    and name in nullified_fields
                                ):
                                    if isinstance(model_field, ManyToManyField):
                                        getattr(obj, name).set([])
                                    else:
                                        setattr(
                                            obj, name, None if model_field.null else ""
                                        )
                                elif isinstance(model_field, ManyToManyField):
                                    getattr(obj, name).set(form.cleaned_data[name])
                                elif form.cleaned_data[name] not in (None, ""):
                                    setattr(obj, name, form.cleaned_data[name])
                            obj.full_clean()
                            obj.save()

                            # Handle tags
                            if form.cleaned_data.get("add_tags", None):
                                obj.tags.add(*form.cleaned_data["add_tags"])
                            if form.cleaned_data.get("remove_tags", None):
                                obj.tags.remove(*form.cleaned_data["remove_tags"])

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
        if "actions" in table.base_columns:
            table.columns.hide("actions")
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


class DeleteView(ReturnURLMixin, View):
    model = None
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
                "return_url": self.get_return_url(request, obj),
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

            return redirect(self.get_return_url(request, obj))

        return render(
            request,
            self.template,
            {
                "object": obj,
                "form": form,
                "object_type": self.model._meta.verbose_name,
                "return_url": self.get_return_url(request, obj),
            },
        )


class ModelListView(View):
    queryset = None
    filter = None
    filter_form = None
    table = None
    template = None
    hidden_columns = []
    hidden_filters = []

    def build_queryset(self, request, kwargs):
        return self.queryset

    def alter_queryset(self, request):
        return self.queryset.all()

    def extra_context(self, kwargs):
        return {}

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
        columns = (
            request.user.preferences.get(
                f"tables.{self.table.__name__}.columns".lower()
            )
            if request.user.is_authenticated
            else None
        )
        table = self.table(self.queryset, columns=columns)
        if "pk" in table.base_columns and (
            permissions["add"] or permissions["change"] or permissions["delete"]
        ):
            table.columns.show("pk")

        # Apply pagination
        paginate = {
            "paginator_class": EnhancedPaginator,
            "per_page": get_paginate_count(request),
        }
        RequestConfig(request, paginate).configure(table)

        # Build filter form
        if self.filter_form:
            filter_form = self.filter_form(request.GET, label_suffix="")
            # Remove fields not to be displayed
            for field in self.hidden_filters:
                if field in filter_form.fields:
                    del filter_form.fields[field]
        else:
            filter_form = None

        # Compute the extra context to attach to this view
        extra_context = self.extra_context(kwargs)

        # Set context and render
        context = {
            "table": table,
            "table_configuration_form": TableConfigurationForm(table=table),
            "filter": self.filter,
            "filter_form": filter_form,
            "permissions": permissions,
            "extra_context": extra_context,
        }
        context.update(extra_context)

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        # If no query set has been provided for some reasons
        if not self.queryset:
            self.queryset = self.build_queryset(request, kwargs)

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


class TableImportView(ReturnURLMixin, View):
    custom_formset = None
    form_model = None
    template = "utils/table_import.html"

    def get_objects(self, request):
        return []

    def get(self, request):
        """
        Method used to render the view when form is not submitted.
        """
        objects = self.get_objects(request)
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
            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template,
            {
                "formset": formset,
                "obj_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.get_return_url(request),
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

            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template,
            {
                "formset": formset,
                "obj_type": self.form_model._meta.model._meta.verbose_name,
                "return_url": self.get_return_url(request),
            },
        )


class ObjectChangeList(PermissionRequiredMixin, ModelListView):
    permission_required = "utils.view_objectchange"
    queryset = ObjectChange.objects.select_related("user", "changed_object_type")
    filter = ObjectChangeFilterSet
    filter_form = ObjectChangeFilterForm
    table = ObjectChangeTable
    template = "utils/object_change/list.html"


class ObjectChangeDetails(PermissionRequiredMixin, View):
    permission_required = "utils.view_objectchange"

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


class TagList(PermissionRequiredMixin, ModelListView):
    permission_required = "utils.view_tag"
    queryset = Tag.objects.annotate(
        items=Count("utils_taggeditem_items", distinct=True)
    ).order_by("name")
    filter = TagFilterSet
    filter_form = TagFilterForm
    table = TagTable
    template = "utils/tag/list.html"


class TagAdd(PermissionRequiredMixin, AddOrEditView):
    permission_required = "utils.add_tag"
    model = Tag
    form = TagForm
    return_url = "utils:tag_list"
    template = "utils/tag/add_edit.html"


class TagDetails(PermissionRequiredMixin, View):
    permission_required = "utils.view_tag"

    def get(self, request, slug):
        tag = get_object_or_404(Tag, slug=slug)
        tagged_items = TaggedItem.objects.filter(tag=tag).count()

        return render(
            request, "utils/tag/details.html", {"tag": tag, "items_count": tagged_items}
        )


class TagEdit(PermissionRequiredMixin, AddOrEditView):
    permission_required = "utils.change_tag"
    model = Tag
    form = TagForm
    template = "utils/tag/add_edit.html"


class TagDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "utils.delete_tag"
    model = Tag
    return_url = "utils:tag_list"


class TagBulkDelete(PermissionRequiredMixin, BulkDeleteView):
    permission_required = "utils.delete_tag"
    model = Tag
    queryset = Tag.objects.annotate(
        items=Count("utils_taggeditem_items", distinct=True)
    ).order_by("name")
    filter = TagFilterSet
    table = TagTable


class TagBulkEdit(PermissionRequiredMixin, BulkEditView):
    permission_required = "utils.change_tag"
    queryset = Tag.objects.annotate(
        items=Count("utils_taggeditem_items", distinct=True)
    ).order_by("name")
    filter = TagFilterSet
    table = TagTable
    form = TagBulkEditForm
