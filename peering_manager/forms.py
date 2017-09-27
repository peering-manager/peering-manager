from __future__ import unicode_literals

from django.contrib.auth.forms import AuthenticationForm

from peering.forms import BootstrapMixin


class LoginForm(BootstrapMixin, AuthenticationForm):
    """
    Bootstraped login form.
    """

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['placeholder'] = ''
        self.fields['password'].widget.attrs['placeholder'] = ''
