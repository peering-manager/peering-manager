from messaging.models import Contact, ContactRole
from utils.testing import ViewTestCases


class ContactRoleTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = ContactRole

    @classmethod
    def setUpTestData(cls):
        ContactRole.objects.bulk_create(
            [
                ContactRole(name="Contact Role 1", slug="contact-role-1"),
                ContactRole(name="Contact Role 2", slug="contact-role-2"),
                ContactRole(name="Contact Role 3", slug="contact-role-3"),
            ]
        )

        cls.form_data = {
            "name": "Contact Role X",
            "slug": "contact-role-x",
            "description": "New contact role",
            "tags": [],
        }
        cls.bulk_edit_data = {"description": "Foo"}


class ContactTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Contact

    @classmethod
    def setUpTestData(cls):
        Contact.objects.bulk_create(
            [
                Contact(name="Contact 1"),
                Contact(name="Contact 2"),
                Contact(name="Contact 3"),
            ]
        )

        cls.form_data = {
            "name": "Contact X",
            "comments": "Some comments",
            "tags": [],
        }
        cls.bulk_edit_data = {"comments": "Foo"}
