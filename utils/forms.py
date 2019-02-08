import csv

from django import forms
from django.conf import settings
from django.contrib.auth.models import User

from .constants import *
from .models import ObjectChange


def add_blank_choice(choices):
    """
    Add a blank choice to the beginning of a choices list.
    """
    return ((None, "---------"),) + tuple(choices)


class CustomNullBooleanSelect(forms.NullBooleanSelect):
    """
    Do not enforce True/False when not selecting an option.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.choices = (("1", "---------"), ("2", "Yes"), ("3", "No"))


class BulkEditForm(forms.Form):
    """
    Base form for editing several objects at the same time.
    """

    def __init__(self, model, parent_object=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.parent_object = parent_object
        self.nullable_fields = []

        if hasattr(self.Meta, "nullable_fields"):
            self.nullable_fields = self.Meta.nullable_fields


class BootstrapMixin(forms.BaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = " ".join([css, "form-control"]).strip()

            if field.required:
                field.widget.attrs["required"] = "required"
            if "placeholder" not in field.widget.attrs:
                field.widget.attrs["placeholder"] = field.label


class CSVDataField(forms.CharField):
    """
    A textarea dedicated for CSV data. It will return dictionaries with a
    header/value mapping. Each dictionary represents one line/record.
    """

    widget = forms.Textarea

    def __init__(self, fields, *args, **kwargs):
        self.fields = fields

        super().__init__(*args, **kwargs)

        if not self.label:
            self.label = "CSV Data"
        if not self.initial:
            self.initial = ",".join(fields) + "\n"
        if not self.help_text:
            self.help_text = "Enter the list of column headers followed by one record per line using commas to separate values.<br>Multi-line data and values containing commas have to be wrapped in double quotes."

    def to_python(self, value):
        records = []
        reader = csv.reader(value.splitlines())

        # First line must be the headers
        headers = next(reader)
        for header in headers:
            if header not in self.fields:
                raise forms.ValidationError(
                    'Unexpected column header "{}" found.'.format(header)
                )

        # Parse CSV data
        for i, row in enumerate(reader, start=1):
            if row:
                # Number of columns in the row does not match the number of
                # headers
                if len(row) != len(headers):
                    raise forms.ValidationError(
                        "Row {}: Expected {} columns but found {}".format(
                            i, len(headers), len(row)
                        )
                    )

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
        required=True, widget=forms.HiddenInput(), initial=True
    )


class CSVChoiceField(forms.ChoiceField):
    """
    This field helps to get a database usable value from a human-readable value
    as input.
    """

    def __init__(self, choices, *args, **kwargs):
        super().__init__(choices=choices, *args, **kwargs)
        self.choices = [(label, label) for value, label in choices]
        self.choice_values = {label: value for value, label in choices}

    def clean(self, value):
        value = super().clean(value)

        if not value:
            return None

        if value not in self.choice_values:
            raise forms.ValidationError("Invalid choice: {}".format(value))

        if not self.choice_values[value]:
            return ""

        return self.choice_values[value]


class FilterChoiceIterator(forms.models.ModelChoiceIterator):
    def __iter__(self):
        queryset = self.queryset.all()
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for obj in queryset:
            yield self.choice(obj)


class FilterChoiceFieldMixin(object):
    iterator = FilterChoiceIterator

    def __init__(self, null_label=None, *args, **kwargs):
        self.null_label = null_label
        if "required" not in kwargs:
            kwargs["required"] = False
        if "widget" not in kwargs:
            kwargs["widget"] = forms.SelectMultiple(attrs={"size": 6})
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        label = super().label_from_instance(obj)
        if hasattr(obj, "filter_count"):
            return "{} ({})".format(label, obj.filter_count)
        return label


class FilterChoiceField(FilterChoiceFieldMixin, forms.ModelMultipleChoiceField):
    pass


class ObjectChangeFilterForm(BootstrapMixin, forms.Form):
    model = ObjectChange
    q = forms.CharField(required=False, label="Search")
    time_after = forms.DateTimeField(
        label="After",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "YYYY-MM-DD hh:mm:ss"}),
    )
    time_before = forms.DateTimeField(
        label="Before",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "YYYY-MM-DD hh:mm:ss"}),
    )
    action = forms.ChoiceField(
        choices=add_blank_choice(OBJECT_CHANGE_ACTION_CHOICES), required=False
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.order_by("username"), required=False
    )


class PasswordField(forms.CharField):
    """
    A field used to enter password. The field will hide the password unless the
    reveal button is clicked.
    """

    def __init__(self, password_source="password", render_value=False, *args, **kwargs):
        widget = kwargs.pop("widget", forms.PasswordInput(render_value=render_value))
        label = kwargs.pop("label", "Password")
        help_text = kwargs.pop(
            "help_text",
            "It can be a clear text password or an "
            "encrypted one. It really depends on how you "
            "want to use it. Be aware that it is stored "
            "without encryption in the database.",
        )
        super().__init__(
            widget=widget, label=label, help_text=help_text, *args, **kwargs
        )
        self.widget.attrs["password-source"] = password_source


class SlugField(forms.SlugField):
    """
    An improved SlugField that allows to be automatically generated based on a
    field used as source.
    """

    def __init__(self, slug_source="name", *args, **kwargs):
        label = kwargs.pop("label", "Slug")
        help_text = kwargs.pop(
            "help_text", "Friendly unique shorthand used for URL and config"
        )
        super().__init__(label=label, help_text=help_text, *args, **kwargs)
        self.widget.attrs["slug-source"] = slug_source


class SmallTextarea(forms.Textarea):
    """
    Just to be used as small text area.
    """

    pass


class TextareaField(forms.CharField):
    """
    A textarea with support for GitHub-Flavored Markdown. Exists mostly just to
    add a standard help_text.
    """

    widget = forms.Textarea

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", False)
        super().__init__(required=required, *args, **kwargs)


class YesNoField(forms.BooleanField):
    """
    A BooleanField rendered as a list to select 'Yes' for True and 'No' for
    False.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            widget=forms.Select(
                choices=[(None, "---------"), ("True", "Yes"), ("False", "No")]
            ),
            *args,
            **kwargs
        )
