from django import forms

from utils.forms import TextareaField


class CommentField(TextareaField):
    """
    A textarea with support for GitHub-Flavored Markdown. Note that it does not
    actually do anything special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            label="Comments",
            help_text='<i class="fab fa-markdown"></i> <a href="https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet" target="_blank">GitHub-Flavored Markdown</a> syntax is supported',
            *args,
            **kwargs
        )


class TemplateField(TextareaField):
    """
    A textarea dedicated for template. Note that it does not actually do anything
    special. It just here to add a help text.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            label="Template",
            help_text='<i class="fas fa-info-circle"></i> <a href="https://peering-manager.readthedocs.io/en/latest/config-template/#configuration-template" target="_blank">Jinja2 template</a> syntax is supported',
            *args,
            **kwargs
        )


class IPNetworkFormField(forms.Field):
    widget = forms.TextInput
    default_error_messages = {"invalid": "Enter a valid IP network (CIDR format)."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return None

        if isinstance(value, _BaseNetwork):
            return value

        if isinstance(value, text_type):
            value = value.strip()

        try:
            network = ip_network(value)
        except ValueError:
            raise ValidationError(self.error_messages["invalid"])

        return network
