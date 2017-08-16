from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render

from .forms import LoginForm


def login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            messages.info(request, "Logged in as {}.".format(request.user))
            return redirect('peering:home')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def logout(request):
    auth_logout(request)
    messages.info(request, "You have logged out.")
    return redirect('peering:home')
