from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.test.utils import override_settings
from django.urls import reverse

from utils.enums import ObjectChangeAction
from utils.models import ObjectChange

from .base import ModelTestCase
from .functions import disable_warnings, post_data


class ModelViewTestCase(ModelTestCase):
    """
    Base `TestCase` for model views. Subclass to test individual views.
    """

    def _get_base_url(self):
        """
        Returns the base format for a URL for the test's model.
        """
        return f"{self.model._meta.app_label}:{self.model._meta.model_name}_{{}}"

    def _get_url(self, action, instance=None):
        """
        Returns the URL name for a specific action and optionally a specific instance.
        """
        url_format = self._get_base_url()

        # If no instance was provided, assume we don't need a unique identifier
        if instance is None:
            return reverse(url_format.format(action))
        else:
            return reverse(url_format.format(action), kwargs={"pk": instance.pk})


class ViewTestCases(object):
    class GetObjectViewTestCase(ModelViewTestCase):
        """
        Retrieves a single instance.
        """

        @override_settings(LOGIN_REQUIRED=False)
        def test_get_object_anonymous(self):
            # Make the request as an unauthenticated user
            self.client.logout()
            response = self.client.get(self._get_queryset().first().get_absolute_url())
            self.assertHttpStatus(response, 200)

        @override_settings(LOGIN_REQUIRED=True)
        def test_get_object_without_permission(self):
            instance = self._get_queryset().first()

            # Try GET without permission
            with disable_warnings("django.request"):
                self.assertHttpStatus(self.client.get(instance.get_absolute_url()), 403)

        @override_settings(LOGIN_REQUIRED=True)
        def test_get_object_with_permission(self):
            instance = self._get_queryset().first()

            self.add_permissions("view")

            # Try GET with permission
            self.assertHttpStatus(self.client.get(instance.get_absolute_url()), 200)

    class GetObjectChangelogViewTestCase(ModelViewTestCase):
        """
        View the changelog for an instance.
        """

        @override_settings(LOGIN_REQUIRED=True)
        def test_get_object_changelog(self):
            url = self._get_url("changelog", self._get_queryset().first())
            response = self.client.get(url)
            self.assertHttpStatus(response, 200)

    class CreateObjectViewTestCase(ModelViewTestCase):
        """
        Create a single new instance.
        """

        form_data = {}

        def test_create_object_without_permission(self):
            # Try GET without permission
            with disable_warnings("django.request"):
                self.assertHttpStatus(self.client.get(self._get_url("add")), 403)

            # Try POST without permission
            request = {
                "path": self._get_url("add"),
                "data": post_data(self.form_data),
            }
            response = self.client.post(**request)
            with disable_warnings("django.request"):
                self.assertHttpStatus(response, 403)

        def test_create_object_with_permission(self):
            initial_count = self._get_queryset().count()

            self.add_permissions("add")

            # Try GET with permission
            self.assertHttpStatus(self.client.get(self._get_url("add")), 200)

            # Try POST with permission
            request = {
                "path": self._get_url("add"),
                "data": post_data(self.form_data),
            }
            self.assertHttpStatus(self.client.post(**request), 302)
            self.assertEqual(initial_count + 1, self._get_queryset().count())
            instance = self._get_queryset().order_by("pk").last()
            self.assertInstanceEqual(instance, self.form_data)

            # Verify ObjectChange creation
            objectchanges = ObjectChange.objects.filter(
                changed_object_type=ContentType.objects.get_for_model(instance),
                changed_object_id=instance.pk,
            )
            self.assertEqual(len(objectchanges), 1)
            self.assertEqual(objectchanges[0].action, ObjectChangeAction.CREATE)

    class EditObjectViewTestCase(ModelViewTestCase):
        """
        Edit a single existing instance.
        """

        form_data = {}

        def test_edit_object_without_permission(self):
            instance = self._get_queryset().first()

            # Try GET without permission
            with disable_warnings("django.request"):
                self.assertHttpStatus(
                    self.client.get(self._get_url("edit", instance)), 403
                )

            # Try POST without permission
            request = {
                "path": self._get_url("edit", instance),
                "data": post_data(self.form_data),
            }
            with disable_warnings("django.request"):
                self.assertHttpStatus(self.client.post(**request), 403)

        def test_edit_object_with_permission(self):
            instance = self._get_queryset().first()

            self.add_permissions("change")

            # Try GET with permission
            self.assertHttpStatus(self.client.get(self._get_url("edit", instance)), 200)

            # Try POST with permission
            request = {
                "path": self._get_url("edit", instance),
                "data": post_data(self.form_data),
            }
            self.assertHttpStatus(self.client.post(**request), 302)
            self.assertInstanceEqual(
                self._get_queryset().get(pk=instance.pk), self.form_data
            )

            # Verify ObjectChange creation
            objectchanges = ObjectChange.objects.filter(
                changed_object_type=ContentType.objects.get_for_model(instance),
                changed_object_id=instance.pk,
            )
            self.assertEqual(len(objectchanges), 1)
            self.assertEqual(objectchanges[0].action, ObjectChangeAction.UPDATE)

    class DeleteObjectViewTestCase(ModelViewTestCase):
        """
        Delete a single instance.
        """

        def test_delete_object_without_permission(self):
            instance = self._get_queryset().first()

            # Try GET without permission
            with disable_warnings("django.request"):
                self.assertHttpStatus(
                    self.client.get(self._get_url("delete", instance)), 403
                )

            # Try POST without permission
            request = {
                "path": self._get_url("delete", instance),
                "data": post_data({"confirm": True}),
            }
            with disable_warnings("django.request"):
                self.assertHttpStatus(self.client.post(**request), 403)

        def test_delete_object_with_permission(self):
            instance = self._get_queryset().first()

            self.add_permissions("delete")

            # Try GET with permission
            self.assertHttpStatus(
                self.client.get(self._get_url("delete", instance)), 200
            )

            # Try POST with permission
            request = {
                "path": self._get_url("delete", instance),
                "data": post_data({"confirm": True}),
            }
            self.assertHttpStatus(self.client.post(**request), 302)
            with self.assertRaises(ObjectDoesNotExist):
                self._get_queryset().get(pk=instance.pk)

            # Verify ObjectChange creation
            objectchanges = ObjectChange.objects.filter(
                changed_object_type=ContentType.objects.get_for_model(instance),
                changed_object_id=instance.pk,
            )
            self.assertEqual(len(objectchanges), 1)
            self.assertEqual(objectchanges[0].action, ObjectChangeAction.DELETE)

    class ListObjectsViewTestCase(ModelViewTestCase):
        """
        Retrieve multiple instances.
        """

        @override_settings(LOGIN_REQUIRED=False)
        def test_list_objects_anonymous(self):
            # Make the request as an unauthenticated user
            self.client.logout()
            response = self.client.get(self._get_url("list"))
            self.assertHttpStatus(response, 200)

        @override_settings(LOGIN_REQUIRED=True)
        def test_list_objects_without_permission(self):
            # Try GET without permission
            with disable_warnings("django.request"):
                self.assertHttpStatus(self.client.get(self._get_url("list")), 403)

        @override_settings(LOGIN_REQUIRED=True)
        def test_list_objects_with_permission(self):
            self.add_permissions("view")

            # Try GET with permission
            self.assertHttpStatus(self.client.get(self._get_url("list")), 200)

    class PrimaryObjectViewTestCase(
        GetObjectViewTestCase,
        GetObjectChangelogViewTestCase,
        CreateObjectViewTestCase,
        EditObjectViewTestCase,
        DeleteObjectViewTestCase,
        ListObjectsViewTestCase,
    ):
        """
        `TestCase` suitable for testing all standard `View` functions for primary
        objects.
        """

        maxDiff = None

    class OrganizationalObjectViewTestCase(
        GetObjectViewTestCase,
        CreateObjectViewTestCase,
        EditObjectViewTestCase,
        DeleteObjectViewTestCase,
        ListObjectsViewTestCase,
    ):
        """
        `TestCase` suitable for all organizational objects such as tags.
        """

        maxDiff = None

    class ContextualObjectViewTestCase(
        GetObjectViewTestCase,
        GetObjectChangelogViewTestCase,
        CreateObjectViewTestCase,
        EditObjectViewTestCase,
        DeleteObjectViewTestCase,
    ):
        """
        `TestCase` suitable for all contextual objects (no global list).
        """

        maxDiff = None

    class ReadOnlyObjectViewTestCase(GetObjectViewTestCase, ListObjectsViewTestCase):
        """
        `TestCase` suitable for all objects that are not created by a user.
        """

        maxDiff = None
