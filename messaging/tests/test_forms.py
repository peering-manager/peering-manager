from django.test import TestCase

from messaging.forms import ContactForm, ContactRoleForm, EmailForm


class ContactRoleTest(TestCase):
    def test_contact_role_form(self):
        test = ContactRoleForm(
            data={
                "name": "Contact Role X",
                "slug": "contact-role-x",
                "description": "New contact role",
                "tags": [],
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class ContactTest(TestCase):
    def test_contact_role_form(self):
        test = ContactForm(
            data={
                "name": "Contact X",
                "comments": "Some comments",
                "tags": [],
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class EmailTest(TestCase):
    def test_email_form(self):
        test = EmailForm(
            data={
                "name": "Test",
                "subject": "test_subject",
                "template": "test_template",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
