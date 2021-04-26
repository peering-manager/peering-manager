import uuid

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from extras.models import JobResult
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("extras-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StaticChoiceTest(APITestCase):
    def test_list_static_choices(self):
        url = reverse("extras-api:field-choice-list")
        response = self.client.get(url, **self.header)
        self.assertEqual(len(response.data), 1)


class JobResultTest(
    StandardAPITestCases.GetObjectView, StandardAPITestCases.ListObjectsView
):
    model = JobResult
    brief_fields = ["url", "created", "completed", "user", "status"]

    @classmethod
    def setUpTestData(cls):
        JobResult.objects.create(
            name="test",
            obj_type=ContentType.objects.get_for_model(JobResult),
            user=None,
            job_id=uuid.uuid4(),
        )
