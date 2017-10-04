from __future__ import unicode_literals

import csv

from django import forms


class BootstrapMixin(forms.BaseForm):
    def __init__(self, *args, **kwargs):
        super(BootstrapMixin, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = ' '.join(
                [css, 'form-control']).strip()

            if field.required:
                field.widget.attrs['required'] = 'required'
            if 'placeholder' not in field.widget.attrs:
                field.widget.attrs['placeholder'] = field.label


class CSVDataField(forms.CharField):
    """
    A textarea dedicated for CSV data. It will return dictionaries with a
    header/value mapping. Each dictionary represents one line/record.
    """
    widget = forms.Textarea

    def __init__(self, fields, *args, **kwargs):
        self.fields = fields

        super(CSVDataField, self).__init__(*args, **kwargs)

        if not self.label:
            self.label = 'CSV Data'
        if not self.initial:
            self.initial = ','.join(fields) + '\n'
        if not self.help_text:
            self.help_text = 'Enter the list of column headers followed by one record per line using commas to separate values.<br>Multi-line data and values containing commas have to be wrapped in double quotes.'

    def to_python(self, value):
        # Python 2 compatibility
        if not isinstance(value, str):
            value = value.encode('utf-8')

        records = []
        reader = csv.reader(value.splitlines())

        # First line must be the headers
        headers = next(reader)
        for header in headers:
            if header not in self.fields:
                raise forms.ValidationError(
                    'Unexpected column header "{}" found.'.format(header))

        # Parse CSV data
        for i, row in enumerate(reader, start=1):
            if row:
                # Number of columns in the row does not match the number of headers
                if len(row) != len(headers):
                    raise forms.ValidationError(
                        "Row {}: Expected {} columns but found {}".format(i, len(headers), len(row)))

                # Dissect the row and create a dictionary with it
                row = [col.strip() for col in row]
                record = dict(zip(headers, row))
                records.append(record)

        return records


class ConfirmationForm(BootstrapMixin, forms.Form):
    """
    A generic confirmation form. The form is not valid unless the confirm field
    is checked.
    """
    confirm = forms.BooleanField(
        required=True, widget=forms.HiddenInput(), initial=True)


class SlugField(forms.SlugField):
    """
    An improved SlugField that allows to be automatically generated based on a
    field used as source.
    """

    def __init__(self, slug_source='name', *args, **kwargs):
        label = kwargs.pop('label', 'Slug')
        help_text = kwargs.pop(
            'help_text', 'Friendly unique shorthand used for URL and config')
        super(SlugField, self).__init__(label=label,
                                        help_text=help_text, *args, **kwargs)
        self.widget.attrs['slug-source'] = slug_source
