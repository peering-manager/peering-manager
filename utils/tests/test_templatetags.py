from django.test import TestCase

from peering.models import AutonomousSystem
from utils.templatetags.helpers import *


class TemplateTagsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a_s = AutonomousSystem.objects.create(asn=64520, name="Useless")

    def test_boolean_as_icon(self):
        self.assertEqual(
            '<i class="fas fa-check text-success"></i>', boolean_as_icon(True)
        )
        self.assertEqual(
            '<i class="fas fa-times text-danger"></i>', boolean_as_icon(False)
        )

    def test_get_status(self):
        self.assertEqual("danger", get_status("delete"))
        self.assertEqual("danger", get_status("REMOVE"))
        self.assertEqual("warning", get_status("change"))
        self.assertEqual("success", get_status("add"))
        self.assertEqual("info", get_status("whatever"))

    def test_as_link(self):
        self.assertEqual("Undefined", as_link("Undefined"))
        self.assertIn("href", as_link(self.a_s))

    def test_render_bandwidth_speed(self):
        self.assertEqual("1 Tbps", render_bandwidth_speed(1000000))
        self.assertEqual("1 Gbps", render_bandwidth_speed(1000))
        self.assertEqual("100 Mbps", render_bandwidth_speed(100))

    def test_render_none(self):
        self.assertEqual(1234, render_none(1234))
        self.assertEqual("1234", render_none("1234"))
        self.assertIn("&mdash;", render_none(""))
        self.assertIn("&mdash;", render_none(None))
        self.assertIn("href", render_none(self.a_s))

    def test_contains(self):
        self.assertTrue(contains("test", "t"))
        self.assertFalse(contains("test", "a"))
        self.assertTrue(contains("test", "a,t"))

    def test_notcontains(self):
        self.assertFalse(notcontains("test", "t"))
        self.assertTrue(notcontains("test", "a"))
        self.assertFalse(notcontains("test", "a,t"))

    def test_markdown(self):
        self.assertEqual("<p>Title</p>", markdown("Title"))
        self.assertEqual("<h1>Title</h1>", markdown("# Title"))
        self.assertEqual(
            "&lt;h1&gt;Title&lt;/h1&gt;", markdown("# Title", escape_html=True)
        )

    def test_render_json(self):
        self.assertEqual(
            """{
    "foo": "bar"
}""",
            render_json({"foo": "bar"}),
        )

    def test_title_with_uppers(self):
        self.assertEqual("Title", title_with_uppers("Title"))
        self.assertEqual("Title", title_with_uppers("title"))
        self.assertEqual("Title Title", title_with_uppers("Title title"))

    def test_doc_version(self):
        self.assertTrue("latest", doc_version("v1.5.0-dev"))
        self.assertTrue("v1.5.0", doc_version("v1.5.0"))
