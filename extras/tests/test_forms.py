from django.test import TestCase

from extras.forms import TagForm


class TagTest(TestCase):
    def test_tag_form(self):
        test = TagForm(data={"name": "Test", "slug": "test", "color": "000000"})
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
