import sys

from django.contrib import messages
from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
    update_session_auth_hash,
)
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.views.generic import View

from .forms import LoginForm, UserPasswordChangeForm


def is_user_logged_in(request):
    """
    Returns True if the user is logged in. Returns False otherwise.
    """
    # If user not logged inform him about it
    if not request.user.is_authenticated:
        messages.error(request, "You are not logged in.")
        return False

    return True


class LoginView(View):
    template = "users/login.html"

    def get(self, request):
        form = LoginForm(request)

        return render(request, self.template, {"form": form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            # Check where should the user be redirected
            next_redirect = request.POST.get("next", "")
            if not is_safe_url(url=next_redirect, allowed_hosts=[request.get_host()]):
                next_redirect = reverse("home")

            auth_login(request, form.get_user())
            messages.info(request, "Logged in as {}.".format(request.user))
            return HttpResponseRedirect(next_redirect)

        return render(request, self.template, {"form": form})


class LogoutView(View):
    def get(self, request):
        if is_user_logged_in(request):
            auth_logout(request)
            messages.info(request, "You have logged out.")

        return redirect("home")


class ProfileView(View, LoginRequiredMixin):
    def get(self, request):
        if not is_user_logged_in(request):
            return redirect("home")

        return render(request, "users/profile.html", {"active_tab": "profile"})


class ChangePasswordView(View, LoginRequiredMixin):
    template = "users/change_password.html"

    def get(self, request):
        if not is_user_logged_in(request):
            return redirect("home")

        form = UserPasswordChangeForm(user=request.user)
        context = {"form": form, "active_tab": "password"}

        return render(request, self.template, context)

    def post(self, request):
        if not is_user_logged_in(request):
            return redirect("home")

        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        context = {"form": form, "active_tab": "password"}

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Your password has been successfully changed.")
            return redirect("users:profile")

        return render(request, self.template, context)
