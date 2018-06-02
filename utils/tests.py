from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ViewTestCase(TestCase):
    """
    This class provides various pre-defined functions to test views.
    """

    def setUp(self):
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

    def _check_if_object_exists(self, model, kwargs):
        exists = True
        try:
            model.objects.get(**kwargs)
        except model.DoesNotExist:
            exists = False

        return exists

    def does_object_exist(self, model, kwargs):
        self.assertTrue(self._check_if_object_exists(model, kwargs))

    def does_object_not_exist(self, model, kwargs):
        self.assertFalse(self._check_if_object_exists(model, kwargs))
