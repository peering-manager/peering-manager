import json

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict as _model_to_dict
from django.test import Client, TestCase as _TestCase
from django.urls import reverse, NoReverseMatch
from rest_framework.test import APIClient

from users.models import Token


def json_file_to_python_type(filename):
    with open(filename, mode="r") as f:
        return json.load(f)
    return None


def model_to_dict(instance, fields=None, exclude=None):
    """
    Customized wrapper for Django's built-in model_to_dict(). Does the following:
      - Excludes the instance ID field
      - Exclude any fields prepended with an underscore
      - Convert any assigned tags to a comma-separated string
    """
    _exclude = ["id"]
    if exclude is not None:
        _exclude += exclude

    model_dict = _model_to_dict(instance, fields=fields, exclude=_exclude)

    for key in list(model_dict.keys()):
        if key.startswith("_"):
            del model_dict[key]
        elif key == "tags":
            model_dict[key] = ",".join(sorted([tag.name for tag in model_dict["tags"]]))
        # Convert ManyToManyField to list of instance PKs
        elif (
            model_dict[key]
            and type(model_dict[key]) in (list, tuple)
            and hasattr(model_dict[key][0], "pk")
        ):
            model_dict[key] = [obj.pk for obj in model_dict[key]]

    return model_dict


def post_data(data):
    """
    Takes a dictionary of test data and returns a dict suitable for POSTing.
    """
    r = {}

    for key, value in data.items():
        if value is None:
            r[key] = ""
        elif type(value) in (list, tuple):
            r[key] = value
        else:
            r[key] = str(value)

    return r


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

    def setUp(self):
        """
        Create a superuser and token for API calls.
        """
        self.user = User.objects.create(
            username="testuser", is_staff=True, is_superuser=True
        )
        self.token = Token.objects.create(user=self.user)
        self.header = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}


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

            elif action in ("details", "edit", "delete"):
                if instance is None:
                    raise Exception(
                        f"Resolving {action} URL requires specifying an instance"
                    )
                # Attempt to resolve using slug first
                if hasattr(self.model, "slug"):
                    try:
                        return reverse(
                            url_format.format(action), kwargs={"slug": instance.slug}
                        )
                    except NoReverseMatch:
                        pass
                # Attempt to resolve using asn
                if hasattr(self.model, "asn"):
                    try:
                        return reverse(
                            url_format.format(action), kwargs={"asn": instance.asn}
                        )
                    except NoReverseMatch:
                        pass
                return reverse(url_format.format(action), kwargs={"pk": instance.pk})

            else:
                raise Exception(f"Invalid action for URL resolution: {action}")

        def test_list_objects(self):
            # Attempt to make the request without required permissions
            self.assertStatus(self.client.get(self._get_url("list")), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.view_{self.model._meta.model_name}"
            )
            response = self.client.get(self._get_url("list"))
            self.assertStatus(response, 200)

        def test_get_object(self):
            instance = self.model.objects.first()

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.get(instance.get_absolute_url()), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.view_{self.model._meta.model_name}"
            )
            response = self.client.get(instance.get_absolute_url())
            self.assertStatus(response, 200)

        def test_create_object(self):
            initial_count = self.model.objects.count()
            request = {
                "path": self._get_url("add"),
                "data": post_data(self.form_data),
                "follow": False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.post(**request), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.add_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, 302)

            self.assertEqual(initial_count + 1, self.model.objects.count())
            instance = self.model.objects.order_by("-pk").first()
            self.assertDictEqual(model_to_dict(instance), self.form_data)

        def test_edit_object(self):
            instance = self.model.objects.first()

            request = {
                "path": self._get_url("edit", instance),
                "data": post_data(self.form_data),
                "follow": False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.post(**request), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.change_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, 302)

            instance = self.model.objects.get(pk=instance.pk)
            self.assertDictEqual(model_to_dict(instance), self.form_data)

        def test_delete_object(self):
            instance = self.model.objects.first()

            request = {
                "path": self._get_url("delete", instance),
                "data": {"confirm": True},
                "follow": False,  # Do not follow 302 redirects
            }

            # Attempt to make the request without required permissions
            self.assertStatus(self.client.post(**request), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.delete_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, 302)

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
            self.assertStatus(self.client.post(**request), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.change_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, 302)

            bulk_edit_fields = self.bulk_edit_data.keys()
            for i, instance in enumerate(self.model.objects.filter(pk__in=pk_list)):
                self.assertDictEqual(
                    model_to_dict(instance, fields=bulk_edit_fields),
                    self.bulk_edit_data,
                    msg=f"Instance {i} failed to validate after bulk edit: {instance}",
                )

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
            self.assertStatus(self.client.post(**request), 403)

            # Assign the required permission and submit again
            self.add_permissions(
                f"{self.model._meta.app_label}.delete_{self.model._meta.model_name}"
            )
            response = self.client.post(**request)
            self.assertStatus(response, 302)

            # Check that all objects were deleted
            self.assertEqual(self.model.objects.count(), 0)
