from unittest.mock import patch

from django.test import TestCase, override_settings

from ..functions import call_irr_as_set_resolver, parse_irr_as_set
from .mocked_data import *


class IRRASSetFunctions(TestCase):
    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_call_irr_as_set_resolver(self, mocked_popen):
        prefixes6 = call_irr_as_set_resolver("AS-MOCKED")
        self.assertEqual(1, len(prefixes6))

        prefixes4 = call_irr_as_set_resolver("AS-MOCKED", address_family=4)
        self.assertEqual(1, len(prefixes4))

        # Nothing happens
        call_irr_as_set_resolver("")

        # Make sure an error is raised in case of issue
        with self.assertRaises(ValueError):
            call_irr_as_set_resolver("AS-WRONG")

    def test_parse_irr_as_set(self):
        self.assertEqual(
            [("RIPE", "AS65535:AS-FOO")],
            parse_irr_as_set(65535, "RIPE::AS65535:AS-FOO"),
        )
        self.assertEqual(
            [("", "AS-BAR"), ("", "AS-BARv6")],
            parse_irr_as_set(65535, "AS-BAR AS-BARv6"),
        )
        self.assertEqual(
            [("", "AS65535:AS-MEMBERS")], parse_irr_as_set(65535, "AS65535:AS-MEMBERS")
        )
        self.assertEqual([("", "AS65535")], parse_irr_as_set(65535, ""))
        self.assertEqual([("", "AS65535")], parse_irr_as_set(65535, None))

    @override_settings(BGPQ3_PATH="/bin/bgpq4")
    def test_parse_irr_as_set_bgpq4(self):
        self.assertEqual(
            [("RIPE", "RIPE::AS65535:AS-FOO")],
            parse_irr_as_set(65535, "RIPE::AS65535:AS-FOO"),
        )
        self.assertEqual(
            [("", "AS-BAR"), ("", "AS-BARv6")],
            parse_irr_as_set(65535, "AS-BAR AS-BARv6"),
        )
        self.assertEqual(
            [("", "AS65535:AS-MEMBERS")], parse_irr_as_set(65535, "AS65535:AS-MEMBERS")
        )
        self.assertEqual([("", "AS65535")], parse_irr_as_set(65535, ""))
        self.assertEqual([("", "AS65535")], parse_irr_as_set(65535, None))
