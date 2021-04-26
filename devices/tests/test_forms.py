from django.test import TestCase

from devices.forms import PlatformForm
from devices.models import Platform


class PlatformTest(TestCase):
    def test_platform_form(self):
        test = PlatformForm(data={"name": "No Bug OS", "slug": "nobugos"})
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
