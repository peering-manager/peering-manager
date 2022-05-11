from json import dumps as json_dumps

import django_filters
from django import forms
from django.core.validators import RegexValidator
from django.db import models
from django.forms import BoundField
from django.forms.fields import InvalidJSONInput
from django.forms.fields import JSONField as _JSONField
from django.urls import reverse

from utils.enums import Color

from .widgets import APISelect, APISelectMultiple


def multivalue_field_factory(field_class):
    """
    Transforms a form field into one that accepts multiple values.

    This is used to apply `or` logic when multiple filter values are given while
    maintaining the field's built-in validation.

    Example: /api/peering/autonomous-systems/?asn=64500&asn=64501
    """

    class MultiValueField(field_class):
        widget = forms.SelectMultiple

        def to_python(self, value):
            if not value:
                return []

            # Only ignore `None` and `False`, `0` makes sense
            return [super(field_class, self).to_python(v) for v in value if v or v == 0]

    return type(f"MultiValue{field_class.__name__}", (MultiValueField,), dict())


class TextareaField(forms.CharField):
    """
    A textarea field. Exists mostly just to set it an non-required by default.
    """

    widget = forms.Textarea

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", False)
        super().__init__(required=required, *args, **kwargs)


class ColorSelect(forms.Select):
    """
    Colorize each <option> inside a select widget.
    """

    option_template_name = "widgets/colorselect_option.html"

    def __init__(self, *args, **kwargs):
        from . import add_blank_choice

        kwargs["choices"] = add_blank_choice(Color.choices)
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-color-picker"


class ColorField(models.CharField):
    default_validators = [
        RegexValidator(
            regex="^[0-9a-f]{6}$",
            message="Enter a valid hexadecimal RGB color code.",
            code="invalid",
        )
    ]
    description = "A hexadecimal RGB color code"

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 6
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs["widget"] = ColorSelect
        return super().formfield(**kwargs)


class CommentField(TextareaField):
    """
    A textarea with support for Markdown. Note that it does not actually do anything
    special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            label="Comments",
            help_text='Styling with <a href="https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet" target="_blank"><i class="fab fa-markdown"></i> Markdown</a> is supported',
            *args,
            **kwargs,
        )


class DynamicModelChoiceMixin(object):
    filter = django_filters.ModelChoiceFilter
    widget = APISelect

    def __init__(
        self,
        *args,
        display_field="display",
        query_params=None,
        initial_params=None,
        null_option=None,
        disabled_indicator=None,
        **kwargs,
    ):
        self.display_field = display_field
        self.to_field_name = kwargs.get("to_field_name")
        self.query_params = query_params or {}
        self.initial_params = initial_params or {}
        self.null_option = null_option
        self.disabled_indicator = disabled_indicator

        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = {"display-field": self.display_field}

        # Set value-field attribute if the field specifies to_field_name
        if self.to_field_name:
            attrs["value-field"] = self.to_field_name

        # Set the string used to represent a null option
        if self.null_option is not None:
            attrs["data-null-option"] = self.null_option

        # Set the disabled indicator, if any
        if self.disabled_indicator is not None:
            attrs["disabled-indicator"] = self.disabled_indicator

        # Attach any static query parameters
        for key, value in self.query_params.items():
            widget.add_query_param(key, value)

        return attrs

    def get_bound_field(self, form, field_name):
        bound_field = BoundField(form, self, field_name)

        # Set the initial value based on prescribed child fields (if not set)
        if not self.initial and self.initial_params:
            filter_kwargs = {}
            for kwarg, child_field in self.initial_params.items():
                value = form.initial.get(child_field.lstrip("$"))
                if value:
                    filter_kwargs[kwarg] = value
            if filter_kwargs:
                self.initial = self.queryset.filter(**filter_kwargs).first()

        # Modify the QuerySet of the field before we return it. Limit choices to any
        # data already bound: Options will be populated on-demand via the APISelect
        # widget
        data = bound_field.value()
        if data:
            field_name = getattr(self, "to_field_name") or "pk"
            filter = self.filter(field_name=field_name)
            try:
                self.queryset = filter.filter(self.queryset, data)
            except (TypeError, ValueError):
                # Catch errors caused by invalid initial data
                self.queryset = self.queryset.none()
        else:
            self.queryset = self.queryset.none()

        # Set the data URL on the APISelect widget (if not already set)
        widget = bound_field.field.widget
        if not widget.attrs.get("data-url"):
            data_url = reverse(
                f"{self.queryset.model._meta.app_label}-api:{self.queryset.model._meta.model_name}-list"
            )
            widget.attrs["data-url"] = data_url

        return bound_field

    def widget_attrs(self, widget):
        attrs = {"display-field": self.display_field}

        # Set value-field attribute if the field specifies to_field_name
        if self.to_field_name:
            attrs["value-field"] = self.to_field_name

        # Attach any static query parameters
        for key, value in self.query_params.items():
            widget.add_query_param(key, value)

        # Set the string used to represent a null option
        if self.null_option is not None:
            attrs["data-null-option"] = self.null_option

        # Set the disabled indicator
        if self.disabled_indicator is not None:
            attrs["disabled-indicator"] = self.disabled_indicator

        return attrs


class DynamicModelChoiceField(DynamicModelChoiceMixin, forms.ModelChoiceField):
    """
    Override get_bound_field() to avoid pre-populating field choices with a SQL query.
    The field will be rendered only with choices set via bound data.
    Choices are populated on-demand via the APISelect widget.
    """

    def clean(self, value):
        if self.null_option is not None and value == "null":
            return None
        return super().clean(value)


class DynamicModelMultipleChoiceField(
    DynamicModelChoiceMixin, forms.ModelMultipleChoiceField
):
    """
    A multiple-choice version of DynamicModelChoiceField.
    """

    filter = django_filters.ModelMultipleChoiceFilter
    widget = APISelectMultiple


class JSONField(_JSONField):
    """
    Overrides Django's built-in JSONField to avoid presenting "null" as the default text.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.help_text:
            self.help_text = (
                'Enter data in <a href="https://json.org/">JSON</a> format.'
            )
            self.widget.attrs["placeholder"] = ""

    def prepare_value(self, value):
        if isinstance(value, InvalidJSONInput):
            return value
        if value is None:
            return ""
        return json_dumps(value, sort_keys=True, indent=4)


class PasswordField(forms.CharField):
    """
    A field used to enter password. The field will hide the password unless the
    reveal button is clicked.
    """

    def __init__(self, password_source="password", render_value=False, *args, **kwargs):
        password_input = forms.PasswordInput(
            render_value=render_value,
            attrs={"autocomplete": "new-password"},
        )
        widget = kwargs.pop("widget", password_input)
        label = kwargs.pop("label", "Password")
        empty_value = kwargs.pop("empty_value", None)
        super().__init__(
            widget=widget, label=label, empty_value=empty_value, *args, **kwargs
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


class TemplateField(TextareaField):
    """
    A textarea dedicated for template. Note that it does not actually do anything
    special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        label = kwargs.pop("label", "Template")
        super().__init__(
            label=label,
            help_text='<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templating/" target="_blank">Jinja2 template</a> syntax is supported',
            *args,
            **kwargs,
        )
