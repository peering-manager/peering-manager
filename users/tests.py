from django.urls import reverse

from utils.tests import ViewTestCase


class UsersViewsTestCase(ViewTestCase):
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
