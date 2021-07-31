from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import Token

from .base import TestCase


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
