from messaging.models import Contact, ContactRole, Email
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


class EmailTestCase(ViewTestCases.PrimaryObjectViewTestCase):
    model = Email

    test_bulk_edit_objects = None

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

        cls.form_data = {
            "name": "E-mail 4",
            "subject": "E-mail subject 4",
            "template": "E-mail template 4",
            "comments": "",
            "tags": [],
        }
