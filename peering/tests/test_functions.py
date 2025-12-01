from unittest.mock import patch

from django.test import TestCase, override_settings

from ..functions import *
from .mocked_data import *


class IRRASSetFunctions(TestCase):
    @patch("peering.functions.subprocess.Popen", side_effect=mocked_subprocess_popen)
    def test_call_irr_as_set_resolver(self, mocked_popen):
        prefixes6 = call_irr_as_set_resolver(as_set="AS-MOCKED")
        self.assertEqual(1, len(prefixes6))

        prefixes4 = call_irr_as_set_resolver(as_set="AS-MOCKED", address_family=4)
        self.assertEqual(1, len(prefixes4))

        # Nothing happens
        call_irr_as_set_resolver(as_set="")

        # Make sure an error is raised in case of issue
        with self.assertRaises(UnresolvableIRRObjectError):
            call_irr_as_set_resolver(as_set="AS-WRONG")

    @patch(
        "peering.functions.subprocess.Popen",
        side_effect=mocked_subprocess_popen_as_list,
    )
    def test_call_irr_as_set_as_list_resolver(self, mocked_popen):
        as_list = call_irr_as_set_as_list_resolver(first_as=65535, as_set="AS-MOCKED")
        self.assertEqual(as_list, [65535, 65537, 65538, 65539])

        as_list = call_irr_as_set_as_list_resolver(first_as=65535, as_set="")
        self.assertEqual(as_list, [65535])

        # Make sure an error is raised in case of issue
        with self.assertRaises(UnresolvableIRRObjectError):
            call_irr_as_set_as_list_resolver(first_as=65535, as_set="AS-WRONG")

    def test_parse_irr_as_set(self):
        self.assertEqual(
            [("RIPE", "AS65535:AS-FOO")],
            parse_irr_as_set(asn=65535, irr_as_set="RIPE::AS65535:AS-FOO"),
        )
        self.assertEqual(
            [("", "AS-BAR"), ("", "AS-BARv6")],
            parse_irr_as_set(asn=65535, irr_as_set="AS-BAR AS-BARv6"),
        )
        self.assertEqual(
            [("", "AS65535:AS-MEMBERS")],
            parse_irr_as_set(asn=65535, irr_as_set="AS65535:AS-MEMBERS"),
        )
        self.assertEqual([("", "AS65535")], parse_irr_as_set(asn=65535, irr_as_set=""))
        self.assertEqual(
            [("", "AS65535")], parse_irr_as_set(asn=65535, irr_as_set=None)
        )

    @override_settings(BGPQ3_PATH="/bin/bgpq4")
    @override_settings(BGPQ4_KEEP_SOURCE_IN_SET=True)
    def test_parse_irr_as_set_bgpq4(self):
        self.assertEqual(
            [("RIPE", "AS65535:AS-FOO")],
            parse_irr_as_set(asn=65535, irr_as_set="RIPE::AS65535:AS-FOO"),
        )
        self.assertEqual(
            [("", "AS-BAR"), ("", "AS-BARv6")],
            parse_irr_as_set(asn=65535, irr_as_set="AS-BAR AS-BARv6"),
        )
        self.assertEqual(
            [("", "AS65535:AS-MEMBERS")],
            parse_irr_as_set(asn=65535, irr_as_set="AS65535:AS-MEMBERS"),
        )
        self.assertEqual([("", "AS65535")], parse_irr_as_set(asn=65535, irr_as_set=""))
        self.assertEqual(
            [("", "AS65535")], parse_irr_as_set(asn=65535, irr_as_set=None)
        )
