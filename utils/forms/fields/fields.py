from json import dumps as json_dumps

from django import forms
from django.core.validators import RegexValidator
from django.db import models
from django.forms.fields import InvalidJSONInput
from django.forms.fields import JSONField as _JSONField

from utils.forms.widgets import ColorSelect


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


class JSONField(_JSONField):
    """
    Overrides Django's built-in JSONField to avoid presenting "null" as the default text.
    """

    def __init__(self, *args, **kwargs):
        widget = kwargs.pop("widget", forms.Textarea(attrs={"class": "text-monospace"}))
        super().__init__(*args, widget=widget, **kwargs)
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
        widget = kwargs.pop("widget", forms.Textarea(attrs={"class": "text-monospace"}))
        label = kwargs.pop("label", "Template")
        super().__init__(widget=widget, label=label, *args, **kwargs)

        if not self.help_text:
            self.help_text = '<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templating/" target="_blank">Jinja2 template</a> syntax is supported.'
