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
    admin_username = forms.CharField(label='Username')
    admin_password = forms.CharField(label='Password', widget=forms.PasswordInput, required=True)
    admin_confirm_password = forms.CharField(label='Confirm password', widget=forms.PasswordInput, required=True)
    admin_email = forms.EmailField(label='Email', widget=forms.EmailInput, required=True)
    login_required = forms.BooleanField(initial=True, label='Login required')

    asn = forms.IntegerField(min_value=1, max_value=4294967295, required=True, label='ASN')
    napalm_username = forms.CharField(label='Napalm username')
    napalm_password = forms.CharField(label='Napalm password', widget=forms.PasswordInput)
    napalm_confirm_password = forms.CharField(label='Napalm confirm password', widget=forms.PasswordInput)
    napalm_timeout = forms.IntegerField(min_value=1, label='Napalm timeout', initial=60)

    def clean(self):
        cleaned_data = super(SetupForm, self).clean()

        napalm_password = cleaned_data.get('napalm_password')
        napalm_confirm_password = cleaned_data.get('napalm_confirm_password')
        admin_password = cleaned_data.get('password')
        admin_confirm_password = cleaned_data.get('confirm_password')

        if napalm_password != napalm_confirm_password:
            self.add_error('napalm_confirm_password', "Password does not match")
        if admin_password != admin_confirm_password:
            self.add_error('confirm_password', "Password does not match")
        return cleaned_data
