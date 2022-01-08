from django.test import TestCase

from messaging.models import Email


class EmailTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.email = Email.objects.create(
            name="Test", subject="{{ test }}", template="{{ test }}"
        )

    def test_render(self):
        self.assertEqual(self.email.render({"test": "test"}), ("test", "test"))
        self.email.template = "{% for i in range(5) %}\n{{ i }}\n{% endfor %}"
        self.assertEqual(
            self.email.render({"test": "test"}), ("test", "\n0\n\n1\n\n2\n\n3\n\n4\n")
        )
        self.email.jinja2_trim = True
        self.assertEqual(
            self.email.render({"test": "test"}), ("test", "0\n1\n2\n3\n4\n")
        )
