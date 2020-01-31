import json

from django.contrib.auth.models import User
from rest_framework.test import APITestCase as __APITestCase

from users.models import Token


def json_file_to_python_type(filename):
    with open(filename, mode="r") as f:
        return json.load(f)
    return None


class APITestCase(__APITestCase):
    def setUp(self):
        """
        Create a superuser and token for API calls.
        """
        self.user = User.objects.create(
            username="testuser", is_staff=True, is_superuser=True
        )
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


class MockedResponse(object):
    def __init__(self, status_code=200, ok=True, fixture=None, content=None):
        self.status_code = status_code
        if fixture:
            self.content = self.load_fixture(fixture)
        elif content:
            self.content = json.dumps(content)
        else:
            self.content = None
        self.ok = ok

    def load_fixture(self, path):
        with open(path, "r") as f:
            return f.read()

    def json(self):
        return json.loads(self.content)
