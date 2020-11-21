from unittest.mock import patch

from django.test import TestCase

from peering import call_irr_as_set_resolver, parse_irr_as_set
from peering.tests.mocked_data import *


class IRRASSetFunctions(TestCase):
    @patch("peering.subprocess.Popen", side_effect=mocked_subprocess_popen)
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
            ["AS-MAZOYER-EU"], parse_irr_as_set(201281, "RIPE::AS-MAZOYER-EU")
        )
        self.assertEqual(
            ["AS-HURRICANE", "AS-HURRICANEv6"],
            parse_irr_as_set(6939, "RADB::AS-HURRICANE RADB::AS-HURRICANEv6"),
        )
        self.assertEqual(
            ["AS51706:AS-MEMBERS"], parse_irr_as_set(51706, "AS51706:AS-MEMBERS")
        )
        self.assertEqual(["AS3333"], parse_irr_as_set(3333, ""))
        self.assertEqual(["AS3333"], parse_irr_as_set(3333, None))
