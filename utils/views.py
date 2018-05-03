from __future__ import unicode_literals

from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.forms import Form, ModelMultipleChoiceField, MultipleHiddenInput
from django.forms.formsets import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe
from django.views.generic import View

from django_tables2 import RequestConfig

from .forms import BootstrapMixin, ConfirmationForm, CSVDataField
from .models import UserAction
from .paginators import EnhancedPaginator


class AddOrEditView(LoginRequiredMixin, View):
    model = None
    form = None
    return_url = None
    template = 'utils/object_add_edit.html'

    def get_object(self, kwargs):
        if 'asn' in kwargs:
            # Lookup object by ASN
            return get_object_or_404(self.model, asn=kwargs['asn'])

        if 'slug' in kwargs:
            # Lookup object by slug
            return get_object_or_404(self.model, slug=kwargs['slug'])

        if 'pk' in kwargs:
            # Lookup object by PK
            return get_object_or_404(self.model, pk=kwargs['pk'])

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
        return reverse('home')

    def get(self, request, *args, **kwargs):
        """
        Method used to render the view when form is not submitted.
        """
        obj = self.alter_object(self.get_object(kwargs), request, args, kwargs)
        form = self.form(instance=obj, initial=request.GET)

        return render(request, self.template, {
            'object': obj,
            'object_type': self.model._meta.verbose_name,
            'form': form,
            'return_url': self.get_return_url(obj),
        })

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
            message = 'Created ' if created else 'Modified '
            message = '{} {} {}'.format(
                message, self.model._meta.verbose_name, escape(obj))
            messages.success(request, mark_safe(message))

            # Log the action
            if created:
                UserAction.objects.log_create(request.user, obj, message)
            else:
                UserAction.objects.log_edit(request.user, obj, message)

            # Redirect the user to the current page to create another object
            if '_addanother' in request.POST:
                return redirect(request.get_full_path())

            return redirect(self.get_return_url(obj))

        return render(request, self.template, {
            'object': obj,
            'object_type': self.model._meta.verbose_name,
            'form': form,
            'return_url': self.get_return_url(obj),
        })


class BulkDeleteView(LoginRequiredMixin, View):
    model = None
    queryset = None
    filter = None
    table = None
    template = 'utils/object_bulk_delete.html'
    return_url = 'home'

    def get(self, request):
        return redirect(self.return_url)

    def get_form(self):
        class BulkDeleteForm(ConfirmationForm):
            pk = ModelMultipleChoiceField(
                queryset=self.model.objects.all(), widget=MultipleHiddenInput)

        return BulkDeleteForm

    def filter_by_extra_context(self, queryset, request, kwargs):
        """
        This function provides a way to narrow a queryset based on the request
        and optional arguments. It must return a queryset as well.
        """
        return queryset

    def post(self, request, **kwargs):
        # Determine URL to redirect users
        posted_return_url = request.POST.get('return_url')
        if posted_return_url and is_safe_url(url=posted_return_url, host=request.get_host()):
            self.return_url = posted_return_url

        # Build the list primary keys of the objects to delete
        if request.POST.get('_all') and self.filter is not None:
            pk_list = [obj.pk for obj in self.filter(request.GET, self.filter_by_extra_context(
                self.model.objects.only('pk'), request, kwargs)).qs]
        else:
            pk_list = [int(pk) for pk in request.POST.getlist('pk')]

        form_model = self.get_form()
        if '_confirm' in request.POST:
            form = form_model(request.POST)
            if form.is_valid():
                queryset = self.model.objects.filter(pk__in=pk_list)

                try:
                    deleted_count = queryset.delete(
                    )[1][self.model._meta.label]
                except ProtectedError as e:
                    print(e)
                    return redirect(self.return_url)

                message = 'Deleted {} {}'.format(
                    deleted_count, self.model._meta.verbose_name_plural)
                messages.success(request, message)
                UserAction.objects.log_bulk_delete(
                    request.user, self.model, message)

                return redirect(self.return_url)
        else:
            form = form_model(
                initial={'pk': pk_list, 'return_url': self.return_url})

        # Retrieve objects being deleted
        queryset = self.queryset or self.model.objects.all()
        table = self.table(queryset.filter(pk__in=pk_list), orderable=False)
        if not table.rows:
            messages.warning(request,
                             'No {} were selected for deletion.'.format(
                                 self.model._meta.verbose_name_plural))
            return redirect(self.return_url)

        return render(request, self.template, {
            'form': form,
            'object_type_plural': self.model._meta.verbose_name_plural,
            'table': table,
            'return_url': self.return_url,
        })


class ConfirmationView(LoginRequiredMixin, View):
    return_url = None
    template = None

    def extra_context(self, kwargs):
        return {}

    def process(self, request, kwargs):
        pass

    def get(self, request, *args, **kwargs):
        form = ConfirmationForm(initial=request.GET)
        context = {
            'form': form,
        }
        context.update(self.extra_context(kwargs))

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            return self.process(request, kwargs)

        context = {
            'form': form,
        }
        context.update(self.extra_context(kwargs))

        return render(request, self.template, context)


class DeleteView(LoginRequiredMixin, View):
    model = None
    return_url = None
    template = 'utils/object_delete.html'

    def get_object(self, kwargs):
        if 'asn' in kwargs:
            # Lookup object by ASN
            return get_object_or_404(self.model, asn=kwargs['asn'])

        if 'slug' in kwargs:
            # Lookup object by slug
            return get_object_or_404(self.model, slug=kwargs['slug'])

        if 'pk' in kwargs:
            # Lookup object by PK
            return get_object_or_404(self.model, pk=kwargs['pk'])

        return None

    def get_return_url(self, obj):
        if obj.pk:
            # If the object has an absolute URL, use it
            return obj.get_absolute_url()

        if self.return_url:
            # Otherwise use the default URL if given
            return reverse(self.return_url)

        # Or return to home
        return reverse('home')

    def get(self, request, *args, **kwargs):
        """
        Method used to render the view when form is not submitted.
        """
        obj = self.get_object(kwargs)
        form = ConfirmationForm(initial=request.GET)

        return render(request, self.template, {
            'object': obj,
            'form': form,
            'object_type': self.model._meta.verbose_name,
            'return_url': self.get_return_url(obj),
        })

    def post(self, request, *args, **kwargs):
        """
        The form has been submitted, process it.
        """
        obj = self.get_object(kwargs)
        form = ConfirmationForm(request.POST)

        if form.is_valid():
            obj.delete()

            # Notify the user
            message = 'Deleted {} {}'.format(
                self.model._meta.verbose_name, escape(obj))
            messages.success(request, message)

            # Log the action
            UserAction.objects.log_delete(request.user, obj, message)

            return redirect(self.get_return_url(obj))

        return render(request, self.template, {
            'object': obj,
            'form': form,
            'object_type': self.model._meta.verbose_name,
            'return_url': self.get_return_url(obj),
        })


class ImportView(LoginRequiredMixin, View):
    form_model = None
    return_url = None
    template = 'utils/object_import.html'

    def import_form(self, *args, **kwargs):
        fields = self.form_model().fields.keys()

        class ImportForm(BootstrapMixin, Form):
            csv = CSVDataField(fields=fields)

        return ImportForm(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Method used to render the view when form is not submitted.
        """
        return render(request, self.template, {
            'form': self.import_form(),
            'fields': self.form_model().fields,
            'obj_type': self.form_model._meta.model._meta.verbose_name,
            'return_url': self.return_url,
        })

    def post(self, request, *args, **kwargs):
        """
        The form has been submitted, process it.
        """
        new_objects = []
        form = self.import_form(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    for row, data in enumerate(form.cleaned_data['csv'], start=1):
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
                                    'csv', 'Row {} {}: {}'.format(row, field,
                                                                  err[0]))
                            raise ValidationError('')

                if new_objects:
                    # Notify user of successful import
                    message = 'Imported {} {}'.format(
                        len(new_objects), new_objects[0]._meta.verbose_name_plural)
                    messages.success(request, message)

                    # Log the import action
                    UserAction.objects.log_import(
                        request.user, self.form_model._meta.model, message)

                    return redirect(self.return_url)
            except ValidationError:
                pass

        return render(request, self.template, {
            'form': form,
            'fields': self.form_model().fields,
            'object_type': self.form_model._meta.model._meta.verbose_name,
            'return_url': self.return_url,
        })


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

    def setup_table_columns(self, request, table, kwargs):
        # Show columns if user is authenticated
        if request.user.is_authenticated:
            if 'pk' in table.base_columns:
                table.columns.show('pk')
            if 'actions' in table.base_columns:
                table.columns.show('actions')

    def get(self, request, *args, **kwargs):
        # If no query set has been provided for some reasons
        if not self.queryset:
            self.queryset = self.build_queryset(request, kwargs)

        # If there is a filter, apply it
        if self.filter:
            self.queryset = self.filter(request.GET, self.queryset).qs

        # Alter the queryset if needed
        self.queryset = self.alter_queryset(request)

        # Build the table based on the queryset
        table = self.table(self.queryset)
        self.setup_table_columns(request, table, kwargs)

        # Apply pagination
        paginate = {
            'klass': EnhancedPaginator,
            'per_page': request.GET.get('per_page', settings.PAGINATE_COUNT)
        }
        RequestConfig(request, paginate).configure(table)

        # Set context and render
        context = {
            'table': table,
            'filter': self.filter,
            'filter_form': self.filter_form(request.GET, label_suffix='') if self.filter_form else None,
        }
        context.update(self.extra_context(kwargs))

        return render(request, self.template, context)


class TableImportView(LoginRequiredMixin, View):
    custom_formset = None
    form_model = None
    return_url = None
    template = 'utils/table_import.html'

    def get_objects(self):
        return []

    def get_return_url(self):
        if self.return_url:
            # Use the default URL if given
            return reverse(self.return_url)

        # Or return to home
        return reverse('home')

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
                    self.form_model, formset=self.custom_formset, extra=0)
            formset = ObjectFormSet(initial=objects)
        else:
            messages.info(request, 'No data to import.')
            return redirect(self.get_return_url())

        return render(request, self.template, {
            'formset': formset,
            'obj_type': self.form_model._meta.model._meta.verbose_name,
            'return_url': self.get_return_url(),
        })

    def post(self, request):
        """
        The form has been submitted, process it.
        """
        if not self.custom_formset:
            ObjectFormSet = formset_factory(self.form_model, extra=0)
        else:
            ObjectFormSet = formset_factory(
                self.form_model, formset=self.custom_formset, extra=0)
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
                message = 'Imported {} {}'.format(
                    len(new_objects), new_objects[0]._meta.verbose_name_plural)
                messages.success(request, message)

                # Log the import action
                UserAction.objects.log_import(
                    request.user, self.form_model._meta.model, message)

            return redirect(self.get_return_url())

        return render(request, self.template, {
            'formset': formset,
            'obj_type': self.form_model._meta.model._meta.verbose_name,
            'return_url': self.get_return_url(),
        })
