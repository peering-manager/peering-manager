from django.test import TestCase

from peering import parse_irr_as_set


class IRRASSetFunctions(TestCase):
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
