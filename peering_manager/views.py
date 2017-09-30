from __future__ import unicode_literals

import sys

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.views.generic import View

from .forms import LoginForm


class LoginView(View):
    template = 'auth/login.html'

    def get(self, request):
        form = LoginForm(request)

        return render(request, self.template, {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            # Check where should the user be redirected
            next_redirect = request.POST.get('next', '')
            if not is_safe_url(url=next_redirect, host=request.get_host()):
                next_redirect = reverse('peering:home')

            auth_login(request, form.get_user())
            messages.info(request, "Logged in as {}.".format(request.user))
            return HttpResponseRedirect(next_redirect)

        return render(request, self.template, {'form': form})


class LogoutView(View):
    def get(self, request):
        auth_logout(request)
        messages.info(request, "You have logged out.")
        return redirect('peering:home')


def handle_500(request):
    """
    Custom 500 error handler.
    """
    __type, error, traceback = sys.exc_info()
    return render(request, '500.html', {'exception': str(__type), 'error': error}, status=500)


def trigger_500(request):
    """
    Method to fake trigger a server error for test reporting.
    """
    raise Exception('Manually triggered error.')
