from django.urls import reverse
from rest_framework import status

from messaging.models import Contact, ContactAssignment, ContactRole, Email
from peering.models.models import AutonomousSystem
from utils.testing import APITestCase, StandardAPITestCases


class AppTest(APITestCase):
    def test_root(self):
        response = self.client.get(reverse("messaging-api:api-root"), **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ContactRoleTest(StandardAPITestCases.View):
    model = ContactRole
    brief_fields = ["display", "id", "name", "slug", "url"]
    create_data = [
        {"name": "Contact Role 4", "slug": "contact-role-4"},
        {"name": "Contact Role 5", "slug": "contact-role-5"},
        {"name": "Contact Role 6", "slug": "contact-role-6"},
    ]
    bulk_update_data = {"description": "Foo"}

    @classmethod
    def setUpTestData(cls):
        contact_roles = [
            ContactRole(name="Contact Role 1", slug="contact-role-1"),
            ContactRole(name="Contact Role 2", slug="contact-role-2"),
            ContactRole(name="Contact Role 3", slug="contact-role-3"),
        ]
        ContactRole.objects.bulk_create(contact_roles)


class ContactTest(StandardAPITestCases.View):
    model = Contact
    brief_fields = ["display", "id", "name", "url"]
    bulk_update_data = {"comments": "Foo"}

    @classmethod
    def setUpTestData(cls):
        contacts = [
            Contact(name="Contact 1"),
            Contact(name="Contact 2"),
            Contact(name="Contact 3"),
        ]
        Contact.objects.bulk_create(contacts)

        cls.create_data = [
            {"name": "Contact 4"},
            {"name": "Contact 5"},
            {"name": "Contact 6"},
        ]


class ContactAssignmentTest(StandardAPITestCases.View):
    model = ContactAssignment
    brief_fields = ["contact", "display", "id", "role", "url"]

    @classmethod
    def setUpTestData(cls):
        asns = [
            AutonomousSystem(name="Foo", asn=64501),
            AutonomousSystem(name="Bar", asn=64502),
        ]
        AutonomousSystem.objects.bulk_create(asns)

        contacts = [
            Contact(name="Contact 1"),
            Contact(name="Contact 2"),
            Contact(name="Contact 3"),
            Contact(name="Contact 4"),
            Contact(name="Contact 5"),
            Contact(name="Contact 6"),
        ]
        Contact.objects.bulk_create(contacts)

        contact_roles = [
            ContactRole(name="Contact Role 1", slug="contact-role-1"),
            ContactRole(name="Contact Role 2", slug="contact-role-2"),
            ContactRole(name="Contact Role 3", slug="contact-role-3"),
        ]
        ContactRole.objects.bulk_create(contact_roles)

        contact_assignments = [
            ContactAssignment(
                object=asns[0], contact=contacts[0], role=contact_roles[0]
            ),
            ContactAssignment(
                object=asns[0], contact=contacts[1], role=contact_roles[1]
            ),
            ContactAssignment(
                object=asns[0], contact=contacts[2], role=contact_roles[2]
            ),
        ]
        ContactAssignment.objects.bulk_create(contact_assignments)

        cls.create_data = [
            {
                "content_type": "peering.autonomoussystem",
                "object_id": asns[1].pk,
                "contact": contacts[3].pk,
                "role": contact_roles[0].pk,
            },
            {
                "content_type": "peering.autonomoussystem",
                "object_id": asns[1].pk,
                "contact": contacts[4].pk,
                "role": contact_roles[1].pk,
            },
            {
                "content_type": "peering.autonomoussystem",
                "object_id": asns[1].pk,
                "contact": contacts[5].pk,
                "role": contact_roles[2].pk,
            },
        ]


class EmailTest(StandardAPITestCases.View):
    model = Email
    brief_fields = ["id", "url", "display", "name"]
    create_data = [
        {"name": "Test1", "subject": "test1_subject", "template": "test1_template"},
        {"name": "Test2", "subject": "test2_subject", "template": "test2_template"},
        {"name": "Test3", "subject": "test3_subject", "template": "test3_template"},
    ]
    bulk_update_data = {"template": "{{ autonomous_system.asn }}"}

    @classmethod
    def setUpTestData(cls):
        Email.objects.bulk_create(
            [
                Email(name="Example 1", subject="Example 1", template="example_1"),
                Email(name="Example 2", subject="Example 2", template="example_2"),
                Email(name="Example 3", subject="Example 3", template="example_3"),
            ]
        )
