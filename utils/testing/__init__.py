import ipaddress
import json

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client
from django.test import TestCase as _TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import Token

from .functions import json_file_to_python_type, model_to_dict, post_data


class MockedResponse(object):
    def __init__(
        self, status_code=status.HTTP_200_OK, ok=True, fixture=None, content=None
    ):
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


class TestCase(_TestCase):
    user_permissions = ()

    def setUp(self):
        # Create the test user and assign permissions
        self.user = User.objects.create_user(username="testuser")
        self.add_permissions(*self.user_permissions)

        # Initialize the test client
        self.client = Client()
        self.client.force_login(self.user)

    def add_permissions(self, *names):
        """
        Assign a set of permissions to the test user.
        Accepts permission names in the form <app>.<action>_<model>.
        """
        for name in names:
            app, codename = name.split(".")
            perm = Permission.objects.get(
                content_type__app_label=app, codename=codename
            )
            self.user.user_permissions.add(perm)

    def remove_permissions(self, *names):
        """
        Remove a set of permissions from the test user, if assigned.
        """
        for name in names:
            app, codename = name.split(".")
            perm = Permission.objects.get(
                content_type__app_label=app, codename=codename
            )
            self.user.user_permissions.remove(perm)

    def assertInstanceEqual(self, instance, data, exclude=None, api=False):
        if exclude is None:
            exclude = []

        fields = [k for k in data.keys() if k not in exclude]
        model_dict = model_to_dict(instance, fields=fields, api=api)

        # Omit any dictionary keys which are not instance attributes or have been excluded
        relevant_data = {
            k: v for k, v in data.items() if hasattr(instance, k) and k not in exclude
        }

        self.assertDictEqual(model_dict, relevant_data)

    def assertStatus(self, response, expected_status):
        """
        Provide detail when receiving an unexpected HTTP response.
        """
        response_data = getattr(response, "data", "No data")
        self.assertEqual(
            response.status_code,
            expected_status,
            f"Expected HTTP status {expected_status}; received {response.status_code}: {response_data}",
        )


class APITestCase(TestCase):
    client_class = APIClient
    model = None
    view_namespace = None

    def setUp(self):
        """
        Creates a superuser and token for API calls.
        """
        self.user = User.objects.create(
            username="testuser", is_staff=True, is_superuser=True
        )
        self.token = Token.objects.create(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}

    def _get_view_namespace(self):
        return f"{self.view_namespace or self.model._meta.app_label}-api"

    def _get_detail_url(self, instance):
        viewname = f"{self._get_view_namespace()}:{instance._meta.model_name}-detail"
        return reverse(viewname, kwargs={"pk": instance.pk})

    def _get_list_url(self):
        viewname = f"{self._get_view_namespace()}:{self.model._meta.model_name}-list"
        return reverse(viewname)


class StandardTestCases(object):
    class Filters(TestCase):
        model = None
        filter = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.model is None:
                raise Exception("Test case requires model to be defined")
            if self.filter is None:
                raise Exception("Test case requires filter to be defined")

            self.queryset = self.model.objects.all()

    class Views(TestCase):
        """
        TestCase suitable for testing all standard View functions:
          - List objects
          - View single object
          - Create new object
          - Modify existing object
          - Delete existing object
        """

        model = None
        # Data to use for creating/editing a single object
        form_data = {}
        # Data to use for editing multiple objects
        bulk_edit_data = {}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.model is None:
                raise Exception("Test case requires model to be defined")

        def _get_url(self, action, instance=None):
            """
            Return the URL name for a specific action.
            An instance must be specified for get/edit/delete views.
            """
            url_format = (
                f"{self.model._meta.app_label}:{self.model._meta.model_name}_{{}}"
            )

            if action in ("list", "add", "bulk_edit", "bulk_delete"):
                return reverse(url_format.format(action))
            elif action in ("details", "edit", "delete", "changelog"):
                if instance is None:
                    raise Exception(
                        f"Resolving {action} URL requires specifying an instance"
                    )
                return reverse(url_format.format(action), kwargs={"pk": instance.pk})
            else:
                raise Exception(f"Invalid action for URL resolution: {action}")

        def test_list_objects(self):
            # Attempt to make the request without required permissions
            self.assertStatus(
                self.client.get(self._get_url("list")), status.HTTP_403_FORBIDDEN
            )

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.view_{self.model._meta.model_name}"
            )
            response = self.client.get(self._get_url("list"))
            self.assertStatus(response, status.HTTP_200_OK)

        def test_get_object(self):
            instance = self.model.objects.first()

            # Attempt to make the request without required permissions
            self.assertStatus(
                self.client.get(instance.get_absolute_url()), status.HTTP_403_FORBIDDEN
            )

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.view_{self.model._meta.model_name}"
            )
            response = self.client.get(instance.get_absolute_url())
            self.assertStatus(response, status.HTTP_200_OK)

        def test_changelog_object(self):
            instance = self.model.objects.first()

            # Attempt to make the request without required permissions
            self.assertStatus(
                self.client.get(instance.get_absolute_url()), status.HTTP_403_FORBIDDEN
            )

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.view_{self.model._meta.model_name}"
            )
            response = self.client.get(self._get_url("changelog", instance=instance))
            self.assertStatus(response, status.HTTP_200_OK)

        def test_create_object(self):
            initial_count = self.model.objects.count()
            request = {
                "path": self._get_url("add"),
                "data": post_data(self.form_data),
                "follow": False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.post(**request), status.HTTP_403_FORBIDDEN)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.add_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, status.HTTP_302_FOUND)

            self.assertEqual(initial_count + 1, self.model.objects.count())
            instance = self.model.objects.order_by("-pk").first()
            self.assertInstanceEqual(instance, self.form_data)

        def test_edit_object(self):
            instance = self.model.objects.first()

            request = {
                "path": self._get_url("edit", instance),
                "data": post_data(self.form_data),
                "follow": False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.post(**request), status.HTTP_403_FORBIDDEN)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.change_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, status.HTTP_302_FOUND)

            instance = self.model.objects.get(pk=instance.pk)
            self.assertInstanceEqual(instance, self.form_data)

        def test_delete_object(self):
            instance = self.model.objects.first()

            request = {
                "path": self._get_url("delete", instance),
                "data": {"confirm": True},
                "follow": False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.post(**request), status.HTTP_403_FORBIDDEN)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.delete_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, status.HTTP_302_FOUND)

            with self.assertRaises(ObjectDoesNotExist):
                self.model.objects.get(pk=instance.pk)

        def test_bulk_edit_objects(self):
            pk_list = self.model.objects.values_list("pk", flat=True)

            request = {
                "path": self._get_url("bulk_edit"),
                "data": {"pk": pk_list, "_apply": True},  # Form button
                "follow": False,  # Do not follow 302 redirects
            }

            # Append the form data to the request
            request["data"].update(post_data(self.bulk_edit_data))

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.post(**request), status.HTTP_403_FORBIDDEN)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.change_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, status.HTTP_302_FOUND)

            for i, instance in enumerate(self.model.objects.filter(pk__in=pk_list)):
                self.assertInstanceEqual(instance, self.bulk_edit_data)

        def test_bulk_delete_objects(self):
            pk_list = self.model.objects.values_list("pk", flat=True)

            request = {
                "path": self._get_url("bulk_delete"),
                "data": {
                    "pk": pk_list,
                    "confirm": True,
                    "_confirm": True,  # Form button
                },
                "follow": False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.post(**request), status.HTTP_403_FORBIDDEN)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.delete_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, status.HTTP_302_FOUND)

            # Check that all objects were deleted
            self.assertEqual(self.model.objects.count(), 0)


class StandardAPITestCases(object):
    class GetObjectView(APITestCase):
        def test_get_object(self):
            """
            GET a single object identified by its numeric ID.
            """
            instance = self.model.objects.first()
            url = self._get_detail_url(instance)
            response = self.client.get(url, **self.header)

            self.assertEqual(response.data["id"], instance.pk)

    class ListObjectsView(APITestCase):
        brief_fields = []

        def test_list_objects(self):
            """
            GET a list of objects.
            """
            url = self._get_list_url()
            response = self.client.get(url, **self.header)

            self.assertEqual(len(response.data["results"]), self.model.objects.count())

        def test_list_objects_brief(self):
            """
            GET a list of objects using the "brief" parameter.
            """
            url = f"{self._get_list_url()}?brief=1"
            response = self.client.get(url, **self.header)

            self.assertEqual(len(response.data["results"]), self.model.objects.count())
            self.assertEqual(
                sorted(response.data["results"][0]), sorted(self.brief_fields)
            )

    class CreateObjectView(APITestCase):
        create_data = []

        def test_create_object(self):
            """
            POST a single object.
            """
            initial_count = self.model.objects.count()
            url = self._get_list_url()
            response = self.client.post(
                url, self.create_data[0], format="json", **self.header
            )

            self.assertStatus(response, status.HTTP_201_CREATED)
            self.assertEqual(self.model.objects.count(), initial_count + 1)
            self.assertInstanceEqual(
                self.model.objects.get(pk=response.data["id"]),
                self.create_data[0],
                api=True,
            )

        def test_bulk_create_object(self):
            """
            POST a set of objects in a single request.
            """
            initial_count = self.model.objects.count()
            url = self._get_list_url()
            response = self.client.post(
                url, self.create_data, format="json", **self.header
            )

            self.assertStatus(response, status.HTTP_201_CREATED)
            self.assertEqual(
                self.model.objects.count(), initial_count + len(self.create_data)
            )

    class UpdateObjectView(APITestCase):
        update_data = {}

        def test_update_object(self):
            """
            PATCH a single object identified by its numeric ID.
            """
            instance = self.model.objects.first()
            url = self._get_detail_url(instance)
            update_data = self.update_data or getattr(self, "create_data")[0]
            response = self.client.patch(url, update_data, format="json", **self.header)

            self.assertStatus(response, status.HTTP_200_OK)
            instance.refresh_from_db()
            self.assertInstanceEqual(instance, self.update_data, api=True)

    class DeleteObjectView(APITestCase):
        def test_delete_object(self):
            """
            DELETE a single object identified by its numeric ID.
            """
            instance = self.model.objects.first()
            url = self._get_detail_url(instance)
            response = self.client.delete(url, **self.header)

            self.assertStatus(response, status.HTTP_204_NO_CONTENT)
            self.assertFalse(self.model.objects.filter(pk=instance.pk).exists())

    class View(
        GetObjectView,
        ListObjectsView,
        CreateObjectView,
        UpdateObjectView,
        DeleteObjectView,
    ):
        pass
