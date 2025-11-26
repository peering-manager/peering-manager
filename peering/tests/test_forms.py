from django.test import TestCase

from bgp.models import Relationship
from messaging.models import Email
from net.models import Connection

from ..constants import *
from ..enums import *
from ..forms import *
from ..models import *


class AutonomousSystemTest(TestCase):
    def test_autonomous_system_form(self):
        test = AutonomousSystemForm(data={"asn": 201281, "name": "Guillaume Mazoyer"})
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())

    def test_autonomous_system_email_form(self):
        email = Email.objects.create(name="E-mail", subject="Hello", template="World")
        test = AutonomousSystemEmailForm(
            data={
                "email": email.pk,
                "recipient": ["test@example.net"],
                "cc": ["test@example.com", "null@example.org"],
                "subject": "Hello",
                "body": "World",
            }
        )
        test.fields["recipient"].choices = [("test@example.net", "My Email")]
        test.fields["cc"].choices = [
            ("test@example.com", "Contact #1"),
            ("null@example.org", "Contact #2"),
        ]
        self.assertTrue(test.is_valid())


class DirectPeeringSessionTest(TestCase):
    def setUp(self):
        super().setUp()

        self.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        self.autonomous_system = AutonomousSystem.objects.create(
            asn=64500, name="Dummy"
        )
        self.relationship = Relationship.objects.create(name="Test", slug="test")

    def test_direct_peering_session_form(self):
        test = DirectPeeringSessionForm(
            data={
                "local_autonomous_system": self.local_autonomous_system.pk,
                "autonomous_system": self.autonomous_system.pk,
                "relationship": self.relationship.pk,
                "ip_address": "2001:db8::1",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class InternetExchangeTest(TestCase):
    def setUp(self):
        super().setUp()

        self.local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )

    def test_internet_exchange_form(self):
        test = InternetExchangeForm(
            data={
                "local_autonomous_system": self.local_autonomous_system.pk,
                "name": "Test",
                "slug": "test",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class InternetExchangePeeringSessionTest(TestCase):
    def setUp(self):
        super().setUp()

        local_autonomous_system = AutonomousSystem.objects.create(
            asn=201281, name="Guillaume Mazoyer", affiliated=True
        )
        self.autonomous_system = AutonomousSystem.objects.create(asn=64500, name="Test")
        self.ixp = InternetExchange.objects.create(
            local_autonomous_system=local_autonomous_system, name="Test", slug="test"
        )
        self.ixp_connection = Connection.objects.create(
            vlan=2000, internet_exchange_point=self.ixp
        )

    def test_internet_exchange_peering_session_form(self):
        test = InternetExchangePeeringSessionForm(
            data={
                "autonomous_system": self.autonomous_system.pk,
                "ixp_connection": self.ixp_connection.pk,
                "ip_address": "2001:db8::1",
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())


class RoutingPolicyTest(TestCase):
    def test_routing_policy_form(self):
        test = RoutingPolicyForm(
            data={
                "name": "Test",
                "slug": "test",
                "type": RoutingPolicyType.IMPORT,
                "weight": 0,
                "address_family": 0,
            }
        )
        self.assertTrue(test.is_valid())
        self.assertTrue(test.save())
