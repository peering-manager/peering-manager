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
        response = self.client.get(
            reverse("users:token_edit", kwargs={"pk": self.token.pk})
        )
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so page should work
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(
            reverse("users:token_edit", kwargs={"pk": self.token.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_user_token_delete_view(self):
        response = self.client.get(
            reverse("users:token_delete", kwargs={"pk": self.token.pk})
        )
        # Without been logged -> redirection
        self.assertEqual(response.status_code, 302)

        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in, so page should work
        self.assertTrue(response.context["user"].is_active)
        response = self.client.get(
            reverse("users:token_delete", kwargs={"pk": self.token.pk})
        )
        self.assertEqual(response.status_code, 200)
