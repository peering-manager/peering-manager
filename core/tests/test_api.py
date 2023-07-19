import uuid

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from utils.testing import APITestCase, APIViewTestCases

from ..models import Job


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("core-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class JobTest(APIViewTestCases.GetObjectView, APIViewTestCases.ListObjectsView):
    model = Job
    test_list_objects_brief = None

    @classmethod
    def setUpTestData(cls):
        Job.objects.create(
            name="test",
            object_type=ContentType.objects.get_for_model(Job),
            user=None,
            job_id=uuid.uuid4(),
        )
