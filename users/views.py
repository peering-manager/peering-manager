from django.contrib import messages
from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
    update_session_auth_hash,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import is_safe_url
from django.views.generic import View

from .forms import (
    LoginForm,
    TokenForm,
    UserPasswordChangeForm,
    UserPreferredASChangeForm,
)
from .models import Token
from utils.forms import ConfirmationForm


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


class PreferencesView(View, LoginRequiredMixin):
    template_name = "users/preferences.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "form": UserPreferredASChangeForm(
                    initial={
                        "preferred_autonomous_system": request.user.preferences.get(
                            "context.asn"
                        )
                    }
                ),
                "preferences": request.user.preferences.all(),
                "active_tab": "preferences",
            },
        )

    def post(self, request):
        preferences = request.user.preferences
        data = preferences.all()

        if "_preferred" in request.POST:
            preferences.set(
                "context.asn", request.POST.get("preferred_autonomous_system")
            )
        else:
            # Delete selected preferences
            for key in request.POST.getlist("pk"):
                if key in data:
                    preferences.delete(key)

        preferences.save()
        messages.success(request, "Your preferences have been updated.")

        return redirect("users:preferences")


class ChangePasswordView(View, LoginRequiredMixin):
    template = "users/change_password.html"

    def get(self, request):
        if not is_user_logged_in(request):
            return redirect("home")

        # LDAP users must not change their passwords
        if getattr(request.user, "ldap_username", None):
            return redirect("users:profile")

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


class TokenList(LoginRequiredMixin, View):
    def get(self, request):
        tokens = Token.objects.filter(user=request.user)
        return render(
            request,
            "users/api_tokens.html",
            {"tokens": tokens, "active_tab": "api_tokens"},
        )


class TokenAddEdit(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if pk is not None:
            if not request.user.has_perm("users.change_token"):
                return HttpResponseForbidden()
            token = get_object_or_404(Token.objects.filter(user=request.user), pk=pk)
        else:
            if not request.user.has_perm("users.add_token"):
                return HttpResponseForbidden()
            token = Token(user=request.user)

        form = TokenForm(instance=token)

        return render(
            request,
            "utils/object_add_edit.html",
            {
                "object": token,
                "object_type": token._meta.verbose_name,
                "form": form,
                "return_url": reverse("users:token_list"),
            },
        )

    def post(self, request, pk=None):
        if pk is not None:
            token = get_object_or_404(Token.objects.filter(user=request.user), pk=pk)
            form = TokenForm(request.POST, instance=token)
        else:
            token = Token()
            form = TokenForm(request.POST)

        if form.is_valid():
            token = form.save(commit=False)
            token.user = request.user
            token.save()

            msg = (
                "Modified token {}".format(token)
                if pk
                else "Created token {}".format(token)
            )
            messages.success(request, msg)

            if "_addanother" in request.POST:
                return redirect(request.path)
            else:
                return redirect("users:token_list")

        return render(
            request,
            "utils/object_add_edit.html",
            {
                "object": token,
                "object_type": token._meta.verbose_name,
                "form": form,
                "return_url": reverse("users:token_list"),
            },
        )


class TokenDelete(PermissionRequiredMixin, View):
    permission_required = "users.delete_token"

    def get(self, request, pk):
        token = get_object_or_404(Token.objects.filter(user=request.user), pk=pk)
        initial_data = {"return_url": reverse("users:token_list")}
        form = ConfirmationForm(initial=initial_data)

        return render(
            request,
            "utils/object_delete.html",
            {
                "object": token,
                "object_type": token._meta.verbose_name,
                "form": form,
                "return_url": reverse("users:token_list"),
            },
        )

    def post(self, request, pk):
        token = get_object_or_404(Token.objects.filter(user=request.user), pk=pk)
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            token.delete()
            messages.success(request, "Token deleted")
            return redirect("users:token_list")

        return render(
            request,
            "utils/object_delete.html",
            {
                "object": token,
                "object_type": token._meta.verbose_name,
                "form": form,
                "return_url": reverse("users:token_list"),
            },
        )
