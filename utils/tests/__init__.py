from django.contrib.auth.models import User
from django.urls import reverse

from utils.forms import add_blank_choice
from utils.testing import TestCase

__all__ = ("ViewTestCase",)


class ViewTestCase(TestCase):
    """
    This class provides various pre-defined functions to test views.

    FIXME: Legacy test case
    """

    def setUp(self):
        self.model = None
        self.credentials = {"username": "dummy", "password": "dummy"}
        self.user = User.objects.create_user(
            **self.credentials, is_staff=True, is_superuser=True
        )

    def authenticate_user(self):
        # Login
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        # Should be logged in
        self.assertTrue(response.context["user"].is_active)

    def _check_if_object_exists(self, kwargs):
        try:
            self.model.objects.get(**kwargs)
            return True
        except self.model.DoesNotExist:
            return False

    def does_object_exist(self, kwargs):
        self.assertTrue(self._check_if_object_exists(kwargs))

    def does_object_not_exist(self, kwargs):
        self.assertFalse(self._check_if_object_exists(kwargs))

    def get_request(
        self,
        path,
        params=None,
        data=None,
        expected_status_code=200,
        contains=None,
        notcontains=None,
    ):
        if data is None:
            data = {}
        if params is None:
            params = {}

        # Perform the GET request
        response = self.client.get(reverse(path, kwargs=params), data=data)

        # Ensure that the status code is the expected one
        self.assertEqual(expected_status_code, response.status_code)

        # Ensure that we have the expected string in the view
        if contains:
            self.assertContains(response, contains)

        # Ensure that we do not have the expected string in the view
        if notcontains:
            self.assertNotContains(response, notcontains)

    def post_request(self, path, params=None, data=None, expected_status_code=200):
        if data is None:
            data = {}
        if params is None:
            params = {}

        # Perform the POST request
        response = self.client.post(
            reverse(path, kwargs=params), data=data, follow=True
        )

        # Ensure that the status code is the expected one
        self.assertEqual(expected_status_code, response.status_code)

    def test_add_blank_choice(self):
        choices = ((1, "One"), (2, "Two"))
        choices_with_blank = ((None, "---------"), (1, "One"), (2, "Two"))
        self.assertEqual(choices_with_blank, add_blank_choice(choices))
