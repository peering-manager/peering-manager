from __future__ import unicode_literals

from django.db import transaction
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import Form
from django.shortcuts import redirect, render
from django.views.generic import View

from .forms import BootstrapMixin, CSVDataField


class ImportView(LoginRequiredMixin, View):
    form_model = None
    return_url = None
    template = 'utils/object_import.html'

    def import_form(self, *args, **kwargs):
        fields = self.form_model().fields.keys()

        class ImportForm(BootstrapMixin, Form):
            csv = CSVDataField(fields=fields)

        return ImportForm(*args, **kwargs)

    def get(self, request):
        """
        Method used to render the view when form is not submitted.
        """
        return render(request, self.template, {
            'form': self.import_form(),
            'fields': self.form_model().fields,
            'obj_type': self.form_model._meta.model._meta.verbose_name,
            'return_url': self.return_url,
        })

    def post(self, request):
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
                                    'csv', "Row {} {}: {}".format(row, field, err[0]))
                            raise ValidationError('')

                if new_objects:
                    # Notify user of successful import and redirect
                    messages.success(request, 'Imported {} {}'.format(
                        len(new_objects), new_objects[0]._meta.verbose_name_plural))
                    return redirect(self.return_url)
            except ValidationError:
                pass

        return render(request, self.template, {
            'form': form,
            'fields': self.form_model().fields,
            'object_type': self.form_model._meta.model._meta.verbose_name,
            'return_url': self.return_url,
        })
