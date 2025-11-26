import logging
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import View
from social_core.backends.utils import load_backends

from peering_manager.authentication import get_auth_backend_display, get_saml_idps
from utils.forms import ConfirmationForm

from .forms import LoginForm, TokenForm, UserPasswordChangeForm
from .models import Token, UserPreferences

logger = logging.getLogger("peering.manager.users")


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

    @method_decorator(sensitive_post_parameters("password"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def generate_auth_data(self, name, url, params):
        display_name, icon_name = get_auth_backend_display(name)

        return {
            "display_name": display_name,
            "icon_name": icon_name,
            "icon_is_url": bool(urlparse(icon_name).scheme),
            "url": f"{url}?{urlencode(params)}",
        }

    def get_auth_backends(self, request):
        auth_backends = []
        saml_idps = get_saml_idps()

        for name in load_backends(settings.AUTHENTICATION_BACKENDS):
            url = reverse("social:begin", args=[name])
            params = {}
            if next := request.GET.get("next"):
                params["next"] = next
            if name.lower() == "saml" and saml_idps:
                for idp in saml_idps:
                    params["idp"] = idp
                    data = self.generate_auth_data(name, url, params)
                    data["display_name"] = f"{data['display_name']} ({idp})"
                    auth_backends.append(data)
            else:
                auth_backends.append(self.generate_auth_data(name, url, params))

        return auth_backends

    def get(self, request):
        form = LoginForm(request)

        if request.user.is_authenticated:
            return self.redirect_to_next(request)

        return render(
            request,
            self.template,
            {
                "form": form,
                "auth_backends": self.get_auth_backends(request),
                "login_form_hidden": settings.LOGIN_FORM_HIDDEN,
            },
        )

    def post(self, request):
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            logger.debug("login form validation was successful")

            auth_login(request, form.get_user())
            logger.info(f"user {request.user} successfully authenticated")
            messages.info(request, f"Logged in as {request.user}.")

            # Back fill user preferences with defined defaults
            if not hasattr(request.user, "preferences"):
                UserPreferences(
                    user=request.user, data=settings.DEFAULT_USER_PREFERENCES
                ).save()

            return self.redirect_to_next(request)

        logger.debug(
            f"Login form validation failed for username: {form['username'].value()}"
        )
        return render(request, self.template, {"form": form})

    def redirect_to_next(self, request):
        data = request.POST if request.method == "POST" else request.GET
        redirect_url = data.get("next", settings.BASE_PATH)

        if redirect_url and url_has_allowed_host_and_scheme(
            redirect_url, allowed_hosts=None
        ):
            logger.debug(f"Redirecting user to {redirect_url}")
        else:
            if redirect_url:
                logger.warning(
                    f"ignoring unsafe 'next' URL passed to login form: {redirect_url}"
                )
            redirect_url = reverse("home")

        return HttpResponseRedirect(redirect_url)


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

        return render(request, "users/profile.html", {"tab": "profile"})


class PreferencesView(View, LoginRequiredMixin):
    template_name = "users/preferences.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "preferences": request.user.preferences.all(),
                "tab": "preferences",
            },
        )

    def post(self, request):
        preferences = request.user.preferences
        data = preferences.all()

        if "as_id" in request.POST:
            preferences.set("context.as", request.POST.get("as_id"), commit=True)
            return redirect("home")

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
        context = {"form": form, "tab": "password"}

        return render(request, self.template, context)

    def post(self, request):
        if not is_user_logged_in(request):
            return redirect("home")

        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        context = {"form": form, "tab": "password"}

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
            {"tokens": tokens, "tab": "api_tokens"},
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
            "generic/edit.html",
            {
                "instance": token,
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

            messages.success(
                request, f"{'Modified' if pk else 'Created'} token {token}"
            )

            if "_addanother" in request.POST:
                return redirect(request.path)
            return redirect("users:token_list")

        return render(
            request,
            "generic/edit.html",
            {
                "instance": token,
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
            "generic/object_delete.html",
            {
                "instance": token,
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
            "generic/object_delete.html",
            {
                "instance": token,
                "form": form,
                "return_url": reverse("users:token_list"),
            },
        )
