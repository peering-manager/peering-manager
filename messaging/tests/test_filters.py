from django.test import TestCase

from messaging.filters import ContactFilterSet, ContactRoleFilterSet, EmailFilterSet
from messaging.models import Contact, ContactRole, Email
from utils.testing import BaseFilterSetTests


class ContactRoleTestCase(TestCase, BaseFilterSetTests):
    queryset = ContactRole.objects.all()
    filterset = ContactRoleFilterSet

    @classmethod
    def setUpTestData(cls):
        contact_roles = [
            ContactRole(name="Contact Role 1", slug="contact-role-1"),
            ContactRole(name="Contact Role 2", slug="contact-role-2"),
            ContactRole(name="Contact Role 3", slug="contact-role-3"),
        ]
        ContactRole.objects.bulk_create(contact_roles)

    def test_name(self):
        params = {"name": ["Contact Role 1", "Contact Role 2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_slug(self):
        params = {"slug": ["contact-role-1", "contact-role-2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ContactTestCase(TestCase, BaseFilterSetTests):
    queryset = Contact.objects.all()
    filterset = ContactFilterSet

    @classmethod
    def setUpTestData(cls):
        contacts = [
            Contact(name="Contact 1"),
            Contact(name="Contact 2"),
            Contact(name="Contact 3"),
        ]
        Contact.objects.bulk_create(contacts)

    def test_name(self):
        params = {"name": ["Contact 1", "Contact 2"]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class EmailTestCase(TestCase, BaseFilterSetTests):
    queryset = Email.objects.all()
    filterset = EmailFilterSet

    @classmethod
    def setUpTestData(cls):
        Email.objects.bulk_create(
            [
                Email(
                    name="E-mail 1",
                    subject="E-mail subject 1",
                    template="E-mail template 1",
                ),
                Email(
                    name="E-mail 2",
                    subject="E-mail subject 2",
                    template="E-mail template 2",
                ),
                Email(
                    name="E-mail 3",
                    subject="E-mail subject 3",
                    template="E-mail template 3",
                ),
            ]
        )

    def test_q(self):
        params = {"q": "E-mail 1"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
