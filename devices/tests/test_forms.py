from django.test import TestCase

from ..forms import *


class ConfigurationTest(TestCase):
    def test_configuration_form(self):
        test = ConfigurationForm(data={"name": "Test", "template": "test_template"})
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class PlatformTest(TestCase):
    def test_platform_form(self):
        test = PlatformForm(data={"name": "No Bug OS", "slug": "nobugos"})
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
