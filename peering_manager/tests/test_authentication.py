from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

from utils.testing import TestCase

User = get_user_model()


class ExternalAuthenticationTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="remoteuser1")

    def setUp(self):
        self.client = Client()

    @override_settings(LOGIN_REQUIRED=True)
    def test_remote_auth_disabled(self):
        """
        Test enabling remote authentication with the default configuration.
        """
        headers = {"HTTP_REMOTE_USER": "remoteuser1"}

        self.assertFalse(settings.REMOTE_AUTH_ENABLED)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_REMOTE_USER")

        # Client should not be authenticated
        self.client.get(reverse("home"), follow=True, **headers)
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(REMOTE_AUTH_ENABLED=True, LOGIN_REQUIRED=True)
    def test_remote_auth_enabled(self):
        """
        Test enabling remote authentication with the default configuration.
        """
        headers = {"HTTP_REMOTE_USER": "remoteuser1"}

        self.assertTrue(settings.REMOTE_AUTH_ENABLED)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_REMOTE_USER")

        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            self.user.pk,
            msg="Authentication failed",
        )

    @override_settings(
        REMOTE_AUTH_ENABLED=True, REMOTE_AUTH_HEADER="HTTP_FOO", LOGIN_REQUIRED=True
    )
    def test_remote_auth_custom_header(self):
        """
        Test enabling remote authentication with a custom HTTP header.
        """
        headers = {"HTTP_FOO": "remoteuser1"}

        self.assertTrue(settings.REMOTE_AUTH_ENABLED)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_FOO")

        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            self.user.pk,
            msg="Authentication failed",
        )

    @override_settings(REMOTE_AUTH_ENABLED=True, LOGIN_REQUIRED=True)
    def test_remote_auth_user_profile(self):
        """
        Test remote authentication with user profile details.
        """
        headers = {
            "HTTP_REMOTE_USER": "remoteuser1",
            "HTTP_REMOTE_USER_FIRST_NAME": "John",
            "HTTP_REMOTE_USER_LAST_NAME": "Smith",
            "HTTP_REMOTE_USER_EMAIL": "johnsmith@example.com",
        }

        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)

        self.user = User.objects.get(username="remoteuser1")
        self.assertEqual(
            self.user.first_name, "John", msg="User first name was not updated"
        )
        self.assertEqual(
            self.user.last_name, "Smith", msg="User last name was not updated"
        )
        self.assertEqual(
            self.user.email, "johnsmith@example.com", msg="User email was not updated"
        )

    @override_settings(
        REMOTE_AUTH_ENABLED=True, REMOTE_AUTH_AUTO_CREATE_USER=True, LOGIN_REQUIRED=True
    )
    def test_remote_auth_auto_create(self):
        """
        Test enabling remote authentication with automatic user creation disabled.
        """
        headers = {"HTTP_REMOTE_USER": "remoteuser2"}

        self.assertTrue(settings.REMOTE_AUTH_ENABLED)
        self.assertTrue(settings.REMOTE_AUTH_AUTO_CREATE_USER)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_REMOTE_USER")

        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)

        # Local user should have been automatically created
        new_user = User.objects.get(username="remoteuser2")
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            new_user.pk,
            msg="Authentication failed",
        )

    @override_settings(
        REMOTE_AUTH_ENABLED=True,
        REMOTE_AUTH_AUTO_CREATE_USER=True,
        REMOTE_AUTH_DEFAULT_GROUPS=["Group 1", "Group 2"],
        LOGIN_REQUIRED=True,
    )
    def test_remote_auth_default_groups(self):
        """
        Test enabling remote authentication with the default configuration.
        """
        headers = {"HTTP_REMOTE_USER": "remoteuser2"}

        self.assertTrue(settings.REMOTE_AUTH_ENABLED)
        self.assertTrue(settings.REMOTE_AUTH_AUTO_CREATE_USER)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_REMOTE_USER")
        self.assertEqual(settings.REMOTE_AUTH_DEFAULT_GROUPS, ["Group 1", "Group 2"])

        # Create required groups
        groups = (Group(name="Group 1"), Group(name="Group 2"), Group(name="Group 3"))
        Group.objects.bulk_create(groups)

        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)

        new_user = User.objects.get(username="remoteuser2")
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            new_user.pk,
            msg="Authentication failed",
        )
        self.assertListEqual([groups[0], groups[1]], list(new_user.groups.all()))

    @override_settings(
        REMOTE_AUTH_ENABLED=True,
        REMOTE_AUTH_AUTO_CREATE_USER=True,
        REMOTE_AUTH_DEFAULT_PERMISSIONS=["devices.add_router", "devices.change_router"],
        LOGIN_REQUIRED=True,
    )
    def test_remote_auth_default_permissions(self):
        """
        Test enabling remote authentication with the default configuration.
        """
        headers = {"HTTP_REMOTE_USER": "remoteuser2"}

        self.assertTrue(settings.REMOTE_AUTH_ENABLED)
        self.assertTrue(settings.REMOTE_AUTH_AUTO_CREATE_USER)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_REMOTE_USER")
        self.assertEqual(
            settings.REMOTE_AUTH_DEFAULT_PERMISSIONS,
            ["devices.add_router", "devices.change_router"],
        )

        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)

        new_user = User.objects.get(username="remoteuser2")
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            new_user.pk,
            msg="Authentication failed",
        )
        self.assertTrue(
            new_user.has_perms(["devices.add_router", "devices.change_router"])
        )

    @override_settings(
        REMOTE_AUTH_ENABLED=True,
        REMOTE_AUTH_AUTO_CREATE_USER=True,
        REMOTE_AUTH_GROUP_SYNC_ENABLED=True,
        LOGIN_REQUIRED=True,
    )
    def test_remote_auth_remote_groups_default(self):
        """
        Test enabling remote authentication with group sync enabled with the default configuration.
        """
        headers = {
            "HTTP_REMOTE_USER": "remoteuser2",
            "HTTP_REMOTE_USER_GROUP": "Group 1|Group 2",
        }

        self.assertTrue(settings.REMOTE_AUTH_ENABLED)
        self.assertTrue(settings.REMOTE_AUTH_AUTO_CREATE_USER)
        self.assertTrue(settings.REMOTE_AUTH_GROUP_SYNC_ENABLED)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_REMOTE_USER")
        self.assertEqual(settings.REMOTE_AUTH_GROUP_HEADER, "HTTP_REMOTE_USER_GROUP")
        self.assertEqual(settings.REMOTE_AUTH_GROUP_SEPARATOR, "|")

        # Create required groups
        groups = (Group(name="Group 1"), Group(name="Group 2"), Group(name="Group 3"))
        Group.objects.bulk_create(groups)

        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)

        new_user = User.objects.get(username="remoteuser2")
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            new_user.pk,
            msg="Authentication failed",
        )
        self.assertListEqual([groups[0], groups[1]], list(new_user.groups.all()))

    @override_settings(
        REMOTE_AUTH_ENABLED=True,
        REMOTE_AUTH_AUTO_CREATE_USER=True,
        REMOTE_AUTH_GROUP_SYNC_ENABLED=True,
        REMOTE_AUTH_AUTO_CREATE_GROUPS=True,
        LOGIN_REQUIRED=True,
    )
    def test_remote_auth_remote_groups_autocreate(self):
        """
        Test enabling remote authentication with group sync and autocreate
        enabled with the default configuration.
        """
        headers = {
            "HTTP_REMOTE_USER": "remoteuser2",
            "HTTP_REMOTE_USER_GROUP": "Group 1|Group 2",
        }

        self.assertTrue(settings.REMOTE_AUTH_ENABLED)
        self.assertTrue(settings.REMOTE_AUTH_AUTO_CREATE_USER)
        self.assertTrue(settings.REMOTE_AUTH_AUTO_CREATE_GROUPS)
        self.assertTrue(settings.REMOTE_AUTH_GROUP_SYNC_ENABLED)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_REMOTE_USER")
        self.assertEqual(settings.REMOTE_AUTH_GROUP_HEADER, "HTTP_REMOTE_USER_GROUP")
        self.assertEqual(settings.REMOTE_AUTH_GROUP_SEPARATOR, "|")

        groups = (Group(name="Group 1"), Group(name="Group 2"))
        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)

        new_user = User.objects.get(username="remoteuser2")
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            new_user.pk,
            msg="Authentication failed",
        )
        self.assertListEqual(
            [group.name for group in groups],
            [group.name for group in list(new_user.groups.all())],
        )

    @override_settings(
        REMOTE_AUTH_ENABLED=True,
        REMOTE_AUTH_AUTO_CREATE_USER=True,
        REMOTE_AUTH_GROUP_SYNC_ENABLED=True,
        REMOTE_AUTH_HEADER="HTTP_FOO",
        REMOTE_AUTH_GROUP_HEADER="HTTP_BAR",
        LOGIN_REQUIRED=True,
    )
    def test_remote_auth_remote_groups_custom_header(self):
        """
        Test enabling remote authentication with group sync enabled with the default configuration.
        """
        headers = {"HTTP_FOO": "remoteuser2", "HTTP_BAR": "Group 1|Group 2"}

        self.assertTrue(settings.REMOTE_AUTH_ENABLED)
        self.assertTrue(settings.REMOTE_AUTH_AUTO_CREATE_USER)
        self.assertTrue(settings.REMOTE_AUTH_GROUP_SYNC_ENABLED)
        self.assertEqual(settings.REMOTE_AUTH_HEADER, "HTTP_FOO")
        self.assertEqual(settings.REMOTE_AUTH_GROUP_HEADER, "HTTP_BAR")
        self.assertEqual(settings.REMOTE_AUTH_GROUP_SEPARATOR, "|")

        # Create required groups
        groups = (Group(name="Group 1"), Group(name="Group 2"), Group(name="Group 3"))
        Group.objects.bulk_create(groups)

        response = self.client.get(reverse("home"), follow=True, **headers)
        self.assertEqual(response.status_code, 200)

        new_user = User.objects.get(username="remoteuser2")
        self.assertEqual(
            int(self.client.session.get("_auth_user_id")),
            new_user.pk,
            msg="Authentication failed",
        )
        self.assertListEqual([groups[0], groups[1]], list(new_user.groups.all()))
