from __future__ import unicode_literals

from django import forms

from .models import AutonomousSystem, Community, ConfigurationTemplate, InternetExchange, PeeringSession, Router
from utils.forms import BootstrapMixin, SlugField


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


class TemplateField(forms.CharField):
    """
    A textarea dedicated for template. Exists mostly just to add a standard help_text.
    """
    widget = forms.Textarea
    default_label = 'Template'
    default_helptext = '<i class="fa fa-info-circle"></i> <a href="https://github.com/respawner/peering-manager/wiki/configuration_template" target="_blank">Jinja2 template</a> syntax is supported'

    def __init__(self, *args, **kwargs):
        required = kwargs.pop('required', False)
        label = kwargs.pop('label', self.default_label)
        help_text = kwargs.pop('help_text', self.default_helptext)
        super(TemplateField, self).__init__(required=required,
                                            label=label, help_text=help_text, *args, **kwargs)


class AutonomousSystemForm(BootstrapMixin, forms.ModelForm):
    comment = CommentField()

    class Meta:
        model = AutonomousSystem
        fields = ('asn', 'name', 'irr_as_set', 'ipv6_max_prefixes',
                  'ipv4_max_prefixes', 'comment',)
        labels = {
            'asn': 'ASN',
            'irr_as_set': 'IRR AS-SET',
            'ipv6_max_prefixes': 'IPv6 Max Prefixes',
            'ipv4_max_prefixes': 'IPv4 Max Prefixes',
            'comment': 'Comments',
        }
        help_texts = {
            'asn': 'BGP autonomous system number (32-bit capable)',
            'name': 'Full name of the AS',
        }


class AutonomousSystemCSVForm(forms.ModelForm):
    class Meta:
        model = AutonomousSystem

        fields = ('asn', 'name', 'irr_as_set', 'ipv6_max_prefixes',
                  'ipv4_max_prefixes', 'comment',)
        labels = {
            'asn': 'ASN',
            'irr_as_set': 'IRR AS-SET',
            'ipv6_max_prefixes': 'IPv6 Max Prefixes',
            'ipv4_max_prefixes': 'IPv4 Max Prefixes',
            'comment': 'Comments',
        }
        help_texts = {
            'asn': 'BGP autonomous system number (32-bit capable)',
            'name': 'Full name of the AS',
        }


class CommunityForm(BootstrapMixin, forms.ModelForm):
    comment = CommentField()

    class Meta:
        model = Community

        fields = ('name', 'value', 'comment',)
        labels = {
            'comment': 'Comments',
        }
        help_texts = {
            'value': 'Community (RFC1997) or Large Community (RFC8092)',
        }


class CommunityCSVForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Community

        fields = ('name', 'value', 'comment',)
        labels = {
            'comment': 'Comments',
        }
        help_texts = {
            'value': 'Community (RFC1997) or Large Community (RFC8092)',
        }


class ConfigurationTemplateForm(BootstrapMixin, forms.ModelForm):
    template = TemplateField()

    class Meta:
        model = ConfigurationTemplate
        fields = ('name', 'template',)


class InternetExchangeForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()
    comment = CommentField()

    class Meta:
        model = InternetExchange
        fields = ('name', 'slug', 'ipv6_address', 'ipv4_address',
                  'configuration_template', 'router', 'comment',)
        labels = {
            'ipv6_address': 'IPv6 Address',
            'ipv4_address': 'IPv4 Address',
            'comment': 'Comments',
        }
        help_texts = {
            'name': 'Full name of the Internet Exchange point',
            'ipv6_address': 'IPv6 Address used to peer',
            'ipv4_address': 'IPv4 Address used to peer',
            'configuration_template': 'Template for configuration generation',
            'router': 'Router connected to the Internet Exchange point',
        }


class InternetExchangePeeringDBForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(InternetExchangePeeringDBForm, self).__init__(*args, **kwargs)
        self.fields['peeringdb_id'].widget.attrs['readonly'] = True

    class Meta:
        model = InternetExchange
        fields = ('peeringdb_id', 'name', 'slug',
                  'ipv6_address', 'ipv4_address',)
        labels = {
            'peeringdb_id': 'PeeringDB ID',
            'ipv6_address': 'IPv6 Address',
            'ipv4_address': 'IPv4 Address',
        }
        help_texts = {
            'peeringdb_id': 'ID used by PeeringDB to identify the IX',
            'name': 'Full name of the Internet Exchange point',
            'ipv6_address': 'IPv6 Address used to peer',
            'ipv4_address': 'IPv4 Address used to peer',
        }


class InternetExchangeCSVForm(forms.ModelForm):
    slug = SlugField()

    class Meta:
        model = InternetExchange
        fields = ('name', 'slug', 'ipv6_address', 'ipv4_address',
                  'configuration_template', 'router', 'comment',)
        labels = {
            'ipv6_address': 'IPv6 Address',
            'ipv4_address': 'IPv4 Address',
            'comment': 'Comments',
        }
        help_texts = {
            'name': 'Full name of the Internet Exchange point',
            'ipv6_address': 'IPv6 Address used to peer',
            'ipv4_address': 'IPv4 Address used to peer',
            'configuration_template': 'Template for configuration generation',
            'router': 'Router connected to the Internet Exchange point',
        }


class InternetExchangeCommunityForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = InternetExchange
        fields = ('communities',)

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            # Get the IX object and remove it from kwargs in order to avoid
            # propagating when calling super
            instance = kwargs.pop('instance')
            # Prepare initial communities
            initial = kwargs.setdefault('initial', {})
            # Add primary key for each community
            initial['communities'] = [
                c.pk for c in instance.communities.all()]

        super(InternetExchangeCommunityForm, self).__init__(*args, **kwargs)

    def save(self):
        instance = forms.ModelForm.save(self)
        instance.communities.clear()

        for community in self.cleaned_data['communities']:
            instance.communities.add(community)


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


class RouterForm(BootstrapMixin, forms.ModelForm):
    comment = CommentField()

    class Meta:
        model = Router

        fields = ('name', 'hostname', 'platform', 'comment',)
        labels = {
            'comment': 'Comments',
        }
        help_texts = {
            'hostname': 'Router hostname (must be resolvable) or IP address',
        }


class RouterCSVForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Router

        fields = ('name', 'hostname', 'platform', 'comment',)
        labels = {
            'comment': 'Comments',
        }
        help_texts = {
            'hostname': 'Router hostname (must be resolvable) or IP address',
        }
