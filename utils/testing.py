from django.contrib.auth.models import User
from rest_framework.test import APITestCase as __APITestCase

from users.models import Token


class APITestCase(__APITestCase):
    def setUp(self):
        """
        Create a superuser and token for API calls.
        """
        self.user = User.objects.create(username="testuser", is_superuser=True)
        self.token = Token.objects.create(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": "Token {}".format(self.token.key)}

    def assertStatus(self, response, expected_status):
        """
        Provide detail when receiving an unexpected HTTP response.
        """
        error_message = "Expected HTTP status {}; received {}: {}"
        self.assertEqual(
            response.status_code,
            expected_status,
            error_message.format(expected_status, response.status_code, response.data),
        )
