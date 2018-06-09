from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ViewTestCase(TestCase):
    """
    This class provides various pre-defined functions to test views.
    """

    def setUp(self):
        self.model = None
        self.credentials = {
            'username': 'dummy',
            'password': 'dummy',
        }
        User.objects.create_user(**self.credentials)

    def authenticate_user(self):
        # Login
        response = self.client.post(reverse('login'), self.credentials,
                                    follow=True)
        # Should be logged in
        self.assertTrue(response.context['user'].is_active)

    def _check_if_object_exists(self, kwargs):
        exists = True

        try:
            self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            exists = False

        return exists

    def does_object_exist(self, kwargs):
        self.assertTrue(self._check_if_object_exists(kwargs))

    def does_object_not_exist(self, kwargs):
        self.assertFalse(self._check_if_object_exists(kwargs))

    def get_request(self, path, params={}, expected_status_code=200,
                    contains=None, notcontains=None):
        # Perform the GET request
        response = self.client.get(reverse(path, kwargs=params))

        # Ensure that the status code is the expected one
        self.assertEqual(expected_status_code, response.status_code)

        # Ensure that we have the expected string in the view
        if contains:
            self.assertContains(response, contains)

        # Ensure that we do not have the expected string in the view
        if notcontains:
            self.assertNotContains(response, notcontains)

    def post_request(self, path, params={}, data={}, expected_status_code=200):
        # Perform the POST request
        response = self.client.post(reverse(path, kwargs=params), data=data,
                                    follow=True)

        # Ensure that the status code is the expected one
        self.assertEqual(expected_status_code, response.status_code)
