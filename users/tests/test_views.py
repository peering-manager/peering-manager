from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse

from utils.tests import ViewTestCase

from ..models import Token


class UserTestCase(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.token = Token.objects.create(user=self.user)

    def test_login_view(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in
        self.assertTrue(response.context["user"].is_active)
        self.assertEqual(response.status_code, 200)

    @override_settings(SOCIAL_AUTH_SAML_ENABLED_IDPS={"idp-a": {}, "idp-b": {}})
    @patch("users.views.load_backends", return_value={"github": None, "saml": None})
    def test_login_view_sso_buttons(self, _):
        response = self.client.get(reverse("login"), {"next": "/peering/autonomous-systems/"})
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        github_url = reverse("social:begin", args=["github"])
        saml_url = reverse("social:begin", args=["saml"])

        # The begin view only accepts POST so each button must be a form, not a link
        self.assertNotIn(f'href="{github_url}', content)
        self.assertIn(f'<form action="{github_url}" method="post">', content)
        self.assertIn('name="csrfmiddlewaretoken"', content)
        self.assertEqual(405, self.client.get(github_url).status_code)

        self.assertIn('<input type="hidden" name="next" value="/peering/autonomous-systems/" />', content)
        for idp in ("idp-a", "idp-b"):
            self.assertIn(f'<input type="hidden" name="idp" value="{idp}" />', content)

        saml_backends = [b for b in response.context["auth_backends"] if b["url"] == saml_url]
        self.assertEqual(["idp-a", "idp-b"], [b["params"]["idp"] for b in saml_backends])

    def test_logout_view(self):
        response = self.client.get(reverse("logout"))
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so logout should work too
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)

    def test_user_profile_view(self):
        response = self.client.get(reverse("users:profile"))
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so page should work
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(reverse("users:profile"))
        self.assertEqual(response.status_code, 200)

    def test_user_change_password_view(self):
        response = self.client.get(reverse("users:change_password"))
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so page should work
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(reverse("users:change_password"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(self.client.get(reverse("users:profile")), reverse("users:change_password"))

        # A user that single sign-on or LDAP authenticates has no local password
        remote_user = User.objects.create_user(username="remote")
        self.assertFalse(remote_user.has_usable_password())
        self.client.force_login(remote_user)
        self.assertNotContains(self.client.get(reverse("users:profile")), reverse("users:change_password"))
        for method in (self.client.get, self.client.post):
            self.assertRedirects(method(reverse("users:change_password")), reverse("users:profile"))

    def test_user_token_list_view(self):
        response = self.client.get(reverse("users:token_list"))
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so page should work
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(reverse("users:token_list"))
        self.assertEqual(response.status_code, 200)

    def test_user_token_add_view(self):
        response = self.client.get(reverse("users:token_add"))
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so page should work
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(reverse("users:token_add"))
        self.assertEqual(response.status_code, 200)

    def test_user_token_edit_view(self):
        response = self.client.get(reverse("users:token_edit", kwargs={"pk": self.token.pk}))
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so page should work
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(reverse("users:token_edit", kwargs={"pk": self.token.pk}))
        self.assertEqual(response.status_code, 200)

    def test_user_token_delete_view(self):
        response = self.client.get(reverse("users:token_delete", kwargs={"pk": self.token.pk}))
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so page should work
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(reverse("users:token_delete", kwargs={"pk": self.token.pk}))
        self.assertEqual(response.status_code, 200)
