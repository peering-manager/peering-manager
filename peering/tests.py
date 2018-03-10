from __future__ import unicode_literals

from django.test import TestCase

from .models import AutonomousSystem


class AutonomousSystemTestCase(TestCase):
    def test_does_exist(self):
        asn = 29467

        # AS should not exist
        autonomous_system = AutonomousSystem.does_exist(asn)
        self.assertEqual(None, autonomous_system)

        # Create the AS
        values = {
            'asn': asn,
            'name': 'LuxNetwork S.A.',
        }
        new_as = AutonomousSystem(**values)
        new_as.save()

        # AS must exist
        autonomous_system = AutonomousSystem.does_exist(asn)
        self.assertEqual(asn, new_as.asn)

    def test_create_from_peeringdb(self):
        asn = 29467

        # Create the AS
        autonomous_system1 = AutonomousSystem.create_from_peeringdb(29467)
        self.assertEqual(29467, autonomous_system1.asn)

        # Must not rise error, just return the AS
        autonomous_system2 = AutonomousSystem.create_from_peeringdb(29467)
        self.assertEqual(29467, autonomous_system2.asn)
