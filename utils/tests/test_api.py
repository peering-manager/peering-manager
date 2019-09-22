from django.urls import reverse

from rest_framework import status

from utils.models import Tag
from utils.testing import APITestCase


class TagTest(APITestCase):
    def setUp(self):
        super().setUp()

        self.tag = Tag.objects.create(name="Test", slug="Test", color="000000")

    def test_get_tag(self):
        url = reverse("utils-api:tag-detail", kwargs={"pk": self.tag.pk})
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["name"], self.tag.name)

    def test_list_tags(self):
        url = reverse("utils-api:tag-list")
        response = self.client.get(url, **self.header)

        self.assertEqual(response.data["count"], 1)

    def test_create_tag(self):
        data = {"name": "Endgame", "slug": "endgame"}

        url = reverse("utils-api:tag-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Tag.objects.count(), 2)
        tag = Tag.objects.get(pk=response.data["id"])
        self.assertEqual(tag.name, data["name"])

    def test_create_tag_bulk(self):
        data = [
            {"name": "Infinity War", "slug": "infinity-war"},
            {"name": "Endgame", "slug": "endgame"},
        ]

        url = reverse("utils-api:tag-list")
        response = self.client.post(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(Tag.objects.count(), 3)
        self.assertEqual(response.data[0]["name"], data[0]["name"])
        self.assertEqual(response.data[1]["name"], data[1]["name"])

    def test_update_tag(self):
        data = {"name": "Test", "slug": "test", "color": "ffffff"}

        url = reverse("utils-api:tag-detail", kwargs={"pk": self.tag.pk})
        response = self.client.put(url, data, format="json", **self.header)

        self.assertStatus(response, status.HTTP_200_OK)
        self.assertEqual(Tag.objects.count(), 1)
        tag = Tag.objects.get(pk=response.data["id"])
        self.assertEqual(tag.color, data["color"])

    def test_delete_autonomous_system(self):
        url = reverse("utils-api:tag-detail", kwargs={"pk": self.tag.pk})
        response = self.client.delete(url, **self.header)

        self.assertStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Tag.objects.count(), 0)
