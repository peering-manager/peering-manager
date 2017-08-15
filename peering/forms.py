from __future__ import unicode_literals

from django import forms

from .models import AutonomousSystem, InternetExchange, PeeringSession


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


class CommentField(forms.CharField):
    """
    A textarea with support for GitHub-Flavored Markdown. Exists mostly just to add a standard help_text.
    """
    widget = forms.Textarea
    default_label = 'Comments'
    default_helptext = '<i class="fa fa-info-circle"></i> <a href="https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet" target="_blank">GitHub-Flavored Markdown</a> syntax is supported'

    def __init__(self, *args, **kwargs):
        required = kwargs.pop('required', False)
        label = kwargs.pop('label', self.default_label)
        help_text = kwargs.pop('help_text', self.default_helptext)
        super(CommentField, self).__init__(required=required,
                                           label=label, help_text=help_text, *args, **kwargs)


class ConfirmationForm(BootstrapMixin, forms.Form):
    """
    A generic confirmation form. The form is not valid unless the confirm field is checked
    """
    confirm = forms.BooleanField(
        required=True, widget=forms.HiddenInput(), initial=True)


class AutonomousSystemForm(BootstrapMixin, forms.ModelForm):
    comment = CommentField()

    class Meta:
        model = AutonomousSystem
        fields = ('asn', 'name', 'ipv6_as_set', 'ipv4_as_set',
                  'ipv6_max_prefixes', 'ipv4_max_prefixes', 'comment',)
        labels = {
            'asn': 'ASN',
            'ipv6_as_set': 'IPv6 AS-SET',
            'ipv4_as_set': 'IPv4 AS-SET',
            'ipv6_max_prefixes': 'IPv6 Max Prefixes',
            'ipv4_max_prefixes': 'IPv4 Max Prefixes',
            'comment': 'Comments',
        }
        help_texts = {
            'asn': 'BGP autonomous system number (32-bit capable)',
            'name': 'Full name of the AS',
        }


class InternetExchangeForm(BootstrapMixin, forms.ModelForm):
    comment = CommentField()

    class Meta:
        model = InternetExchange
        fields = ('name', 'slug', 'comment',)
        labels = {
            'comment': 'Comments',
        }
        help_texts = {
            'name': 'Full name of the Internet Exchange point',
            'slug': 'Router configuration and URL friendly shorthand',
        }


class PeeringSessionForm(BootstrapMixin, forms.ModelForm):
    comment = CommentField()

    class Meta:
        model = PeeringSession
        fields = ('autonomous_system', 'internet_exchange',
                  'ip_address', 'comment',)
        labels = {
            'autonomous_system': 'ASN',
            'internet_exchange': 'IX',
            'ip_address': 'IP Address',
            'comment': 'Comments',
        }
        help_texts = {
            'ip_address': 'IPv6 or IPv4 address',
        }
