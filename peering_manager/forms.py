from __future__ import unicode_literals

from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django import forms

from utils.forms import BootstrapMixin
from django.conf import settings


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
    napalm_username = forms.CharField(label='Napalm username')
    napalm_password = forms.CharField(label='Napalm password', widget=forms.PasswordInput)
    napalm_timeout = forms.IntegerField(min_value=1, label='Napalm timeout', initial=60)
    login_required = forms.BooleanField(initial=True, label='Login required')

