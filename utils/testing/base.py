import json
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ManyToManyField
from django.forms.models import model_to_dict
from django.test import Client
from django.test import TestCase as _TestCase
from rest_framework import status
from taggit.managers import TaggableManager

from .functions import extract_form_failures


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

    def assertHttpStatus(self, response, expected_status):
        """
        Provide detail when receiving an unexpected HTTP response.
        """
        err_message = None
        # Construct an error message only if the test is going to fail
        if response.status_code != expected_status:
            if hasattr(response, "data"):
                # REST API response; pass the response data through directly
                err = response.data
            else:
                # Try to extract form validation errors from the response HTML
                form_errors = extract_form_failures(response.content)
                err = form_errors or response.content or "No data"
            err_message = f"Expected HTTP status {expected_status}; received {response.status_code}: {err}"
        self.assertEqual(response.status_code, expected_status, err_message)


class ModelTestCase(TestCase):
    """
    Parent class for test cases which deal with models.
    """

    model = None

    def add_permissions(self, *names):
        perms = []
        for name in names:
            perms.append(
                f"{self.model._meta.app_label}.{name}_{self.model._meta.model_name}"
            )
        super().add_permissions(*perms)

    def remove_permissions(self, *names):
        perms = []
        for name in names:
            perms.append(
                f"{self.model._meta.app_label}.{name}_{self.model._meta.model_name}"
            )
        super().add_permissions(*perms)

    def _get_queryset(self):
        """
        Returns a base queryset suitable for use in test methods.
        """
        return self.model.objects.all()

    def prepare_instance(self, instance):
        """
        Override this method to perform manipulation of an instance prior to its
        evaluation against test data.
        """
        return instance

    def model_to_dict(self, instance, fields, api=False):
        """
        Returns a dictionary representation of an instance.
        """
        # Prepare the instance and call Django's model_to_dict() to extract all fields
        model_dict = model_to_dict(self.prepare_instance(instance), fields=fields)

        # Map any additional (non-field) instance attributes that were specified
        for attr in fields:
            if hasattr(instance, attr) and attr not in model_dict:
                model_dict[attr] = getattr(instance, attr)

        for key, value in list(model_dict.items()):
            try:
                field = instance._meta.get_field(key)
            except FieldDoesNotExist:
                # Attribute is not a model field
                continue

            # Handle ManyToManyFields
            if value and type(field) in (ManyToManyField, TaggableManager):
                if field.related_model is ContentType:
                    model_dict[key] = sorted(
                        [f"{ct.app_label}.{ct.model}" for ct in value]
                    )
                else:
                    model_dict[key] = sorted([obj.pk for obj in value])

            if api and type(value) in (
                IPv4Address,
                IPv6Address,
                IPv4Interface,
                IPv6Interface,
            ):
                model_dict[key] = str(value)

            if api:
                # Replace ContentType numeric IDs with <app_label>.<model>
                if type(getattr(instance, key)) is ContentType:
                    ct = ContentType.objects.get(pk=value)
                    model_dict[key] = f"{ct.app_label}.{ct.model}"

        return model_dict

    def assertInstanceEqual(self, instance, data, exclude=None, api=False):
        """
        Compares a model instance to a dictionary, checking that its attribute values
        match those specified in the dictionary.
        """
        if exclude is None:
            exclude = []

        fields = [k for k in data.keys() if k not in exclude]
        model_dict = self.model_to_dict(instance, fields=fields, api=api)

        # Omit any dictionary keys which are not instance attributes or have been excluded
        relevant_data = {
            k: v for k, v in data.items() if hasattr(instance, k) and k not in exclude
        }

        self.assertDictEqual(model_dict, relevant_data)
