from __future__ import unicode_literals

import sys

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.views.generic import View

from .forms import LoginForm, UserPasswordChangeForm
from peering.models import (AutonomousSystem, Community,
                            ConfigurationTemplate, InternetExchange, PeeringSession, Router)
from peeringdb.models import Synchronization
from utils.models import UserAction


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
                next_redirect = reverse('home')

            auth_login(request, form.get_user())
            messages.info(request, "Logged in as {}.".format(request.user))
            return HttpResponseRedirect(next_redirect)

        return render(request, self.template, {'form': form})


class LogoutView(View):
    def get(self, request):
        auth_logout(request)
        messages.info(request, "You have logged out.")
        return redirect('home')


class Home(View):
    def get(self, request):
        statistics = {
            'as_count': AutonomousSystem.objects.count(),
            'ix_count': InternetExchange.objects.count(),
            'communities_count': Community.objects.count(),
            'config_templates_count': ConfigurationTemplate.objects.count(),
            'routers_count': Router.objects.count(),
            'peering_sessions_count': PeeringSession.objects.count(),
        }
        context = {
            'statistics': statistics,
            'history': UserAction.objects.select_related('user')[:50],
            'synchronizations': Synchronization.objects.all()[:5],
        }
        return render(request, 'home.html', context)


class ProfileView(View, LoginRequiredMixin):
    def get(self, request):
        return render(request, 'user/profile.html', {'active_tab': 'profile', })


class ChangePasswordView(View, LoginRequiredMixin):
    template = 'user/change_password.html'

    def get(self, request):
        form = UserPasswordChangeForm(user=request.user)
        context = {
            'form': form,
            'active_tab': 'password',
        }

        return render(request, self.template, context)

    def post(self, request):
        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        context = {
            'form': form,
            'active_tab': 'password',
        }

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(
                request, "Your password has been successfully changed.")
            return redirect('user_profile')

        return render(request, self.template, context)


class RecentActivityView(View, LoginRequiredMixin):
    def get(self, request):
        context = {
            'activity': request.user.actions.all()[:50],
            'active_tab': 'activity',
        }
        return render(request, 'user/activity.html', context)


def handle_500(request):
    """
    Custom 500 error handler.
    """
    __type, error, traceback = sys.exc_info()
    del traceback
    return render(request, '500.html', {'exception': str(__type), 'error': error}, status=500)


def trigger_500(request):
    """
    Method to fake trigger a server error for test reporting.
    """
    raise Exception('Manually triggered error.')
