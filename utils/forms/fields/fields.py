import ipaddress
from json import dumps as json_dumps

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count
from django.forms.fields import InvalidJSONInput
from django.forms.fields import JSONField as _JSONField

from ..widgets import ColourSelect, StaticSelectMultiple

__all__ = (
    "ColourField",
    "CommentField",
    "IPNetworkFormField",
    "JSONField",
    "PasswordField",
    "SlugField",
    "TagFilterField",
    "TemplateField",
    "TextareaField",
)


class TextareaField(forms.CharField):
    """
    A textarea field. Exists mostly just to set it an non-required by default.
    """

    widget = forms.Textarea

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", False)
        super().__init__(*args, required=required, **kwargs)


class ColourField(models.CharField):
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
        kwargs["widget"] = ColourSelect
        return super().formfield(**kwargs)


class CommentField(TextareaField):
    """
    A textarea with support for Markdown. Note that it does not actually do anything
    special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            label="Comments",
            help_text='Styling with <a href="https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet" target="_blank"><i class="fab fa-markdown"></i> Markdown</a> is supported',
            **kwargs,
        )


class IPNetworkFormField(forms.Field):
    default_error_messages = {
        "invalid": "Enter a valid IPv4 or IPv6 address (with CIDR mask)."
    }

    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, ipaddress.IPv4Network | ipaddress.IPv6Network):
            return value

        if "/" not in value:
            raise ValidationError("CIDR mask (e.g. /24) is required.")

        try:
            return ipaddress.ip_network(value)
        except ValueError as exc:
            raise ValidationError(
                "Please specify a valid IPv4 or IPv6 network."
            ) from exc


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
            *args, widget=widget, label=label, empty_value=empty_value, **kwargs
        )
        self.widget.attrs["password-source"] = password_source


class SlugField(forms.SlugField):
    """
    An improved SlugField that allows to be automatically generated based on a
    field used as source.
    """

    help_text = "URL-friendly unique shorthand"

    def __init__(self, *, slug_source="name", help_text=help_text, **kwargs):
        super().__init__(help_text=help_text, **kwargs)

        self.widget.attrs["slug-source"] = slug_source


class TagFilterField(forms.MultipleChoiceField):
    """
    A filter field for the tags of a model.
    Only the tags used by a model are displayed.
    """

    widget = StaticSelectMultiple

    def __init__(self, model, *args, **kwargs):
        def get_choices():
            tags = model.tags.annotate(count=Count("extras_taggeditem_items")).order_by(
                "name"
            )
            return [(str(tag.slug), f"{tag.name} ({tag.count})") for tag in tags]

        # Choices are fetched each time the form is initialized
        super().__init__(
            *args, label="Tags", choices=get_choices, required=False, **kwargs
        )


class TemplateField(TextareaField):
    """
    A textarea dedicated for template. Note that it does not actually do anything
    special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        widget = kwargs.pop("widget", forms.Textarea(attrs={"class": "text-monospace"}))
        label = kwargs.pop("label", "Template")
        super().__init__(*args, widget=widget, label=label, **kwargs)

        if not self.help_text:
            self.help_text = '<i class="fa-fw fa-solid fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/templating/" target="_blank">Jinja2 template</a> syntax is supported.'
