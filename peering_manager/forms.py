from __future__ import unicode_literals

from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django import forms

from utils.forms import BootstrapMixin


class LoginForm(BootstrapMixin, AuthenticationForm):
    """
    Bootstraped login form.
    """

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['placeholder'] = ''
        self.fields['password'].widget.attrs['placeholder'] = ''


class UserPasswordChangeForm(BootstrapMixin, PasswordChangeForm):
    pass


class SetupForm(forms.Form):
    """
    Setup page
    """

    asn = forms.IntegerField(min_value=1, max_value=4294967295, required=True, label='ASN')
    secret_key = forms.CharField(required=True, label='Secret key')
    allowed_hosts = forms.CharField(required=True, label='Allowed hosts')
    login_required = forms.BooleanField(initial=True, label='Login required')
    napalm_username = forms.CharField(label='Napalm username')
    napalm_password = forms.CharField(label='Napalm password')
    napalm_timeout = forms.IntegerField(min_value=1, label='Napalm timeout')
