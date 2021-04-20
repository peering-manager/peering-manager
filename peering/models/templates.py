from django.db import models
from django.urls import reverse
from jinja2 import Environment, TemplateSyntaxError

from net.models import Connection
from peering.enums import BGPRelationship, RoutingPolicyType

from .abstracts import Template
from .jinja2 import FILTER_DICT
from .models import (
    AutonomousSystem,
    BGPGroup,
    Community,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    Router,
    RoutingPolicy,
)


class Configuration(Template):
    def get_absolute_url(self):
        return reverse("peering:configuration_details", kwargs={"pk": self.pk})

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        environment = Environment()

        # Add custom filters to our environment
        environment.filters.update(FILTER_DICT)

        # Try rendering the template, return a message about syntax issues if there
        # are any
        try:
            jinja2_template = environment.from_string(self.template)
            return jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            return f"Syntax error in template at line {e.lineno}: {e.message}"
        except Exception as e:
            return str(e)

    def render_preview(self):
        """
        Render the template using Jinja2 for previewing it.
        """
        variables = None

        # Variables for template preview
        my_as = AutonomousSystem(
            asn=64500,
            name="My AS",
            ipv6_max_prefixes=50,
            ipv4_max_prefixes=100,
            affiliated=True,
        )
        a_s = AutonomousSystem(
            asn=64501, name="ACME", ipv6_max_prefixes=50, ipv4_max_prefixes=100
        )
        a_s.tags = ["foo", "bar"]
        i_x = InternetExchange(
            name="Wakanda-IX",
            slug="wakanda-ix",
        )
        i_x.tags = ["foo", "bar"]
        connection = Connection(
            ipv6_address="2001:db8:a::ffff",
            ipv4_address="192.0.2.128",
            internet_exchange_point=i_x,
        )
        group = BGPGroup(name="Transit Providers", slug="transit")
        group.tags = ["foo", "bar"]
        dps6 = DirectPeeringSession(
            local_autonomous_system=my_as,
            autonomous_system=a_s,
            ip_address="2001:db8::1",
            relationship=BGPRelationship.TRANSIT_PROVIDER,
        )
        dps6.tags = ["foo", "bar"]
        dps4 = DirectPeeringSession(
            local_autonomous_system=my_as,
            autonomous_system=a_s,
            ip_address="192.0.2.1",
            relationship=BGPRelationship.PRIVATE_PEERING,
        )
        dps4.tags = ["foo", "bar"]
        ixps6 = InternetExchangePeeringSession(
            autonomous_system=a_s,
            ixp_connection=connection,
            ip_address="2001:db8:a::aaaa",
        )
        ixps6.tags = ["foo", "bar"]
        ixps4 = InternetExchangePeeringSession(
            autonomous_system=a_s, ixp_connection=connection, ip_address="192.0.2.64"
        )
        ixps4.tags = ["foo", "bar"]
        group.sessions = {6: [dps6], 4: [dps4]}
        i_x.sessions = {6: [ixps6], 4: [ixps4]}

        return self.render(
            {
                "my_as": [my_as],
                "bgp_groups": [group],
                "internet_exchanges": [i_x],
                "routing_policies": [
                    RoutingPolicy(
                        name="Export/Import None",
                        slug="none",
                        type=RoutingPolicyType.IMPORT_EXPORT,
                    )
                ],
                "communities": [Community(name="Community Transit", value="64500:1")],
            }
        )


class Email(Template):
    # While a line length should not exceed 78 characters (as per RFC2822), we allow
    # user more characters for templating and let the user to decide what he wants to
    # with this recommended limit, including not respecting it
    subject = models.CharField(max_length=512)

    def get_absolute_url(self):
        return reverse("peering:email_details", kwargs={"pk": self.pk})

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        subject = ""
        body = ""
        environment = Environment()

        try:
            jinja2_template = environment.from_string(self.subject)
            subject = jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            subject = (
                f"Syntax error in subject template at line {e.lineno}: {e.message}"
            )
        except Exception as e:
            subject = str(e)

        try:
            jinja2_template = environment.from_string(self.template)
            body = jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            body = f"Syntax error in body template at line {e.lineno}: {e.message}"
        except Exception as e:
            body = str(e)

        return subject, body

    def render_preview(self):
        """
        Render the template using Jinja2 for previewing it.
        """
        variables = None

        # Variables for template preview
        my_as = AutonomousSystem(
            asn=64500,
            name="My AS",
            ipv6_max_prefixes=50,
            ipv4_max_prefixes=100,
            affiliated=True,
        )
        a_s = AutonomousSystem(
            asn=64501, name="ACME", ipv6_max_prefixes=50, ipv4_max_prefixes=100
        )
        a_s.tags = ["foo", "bar"]
        i_x = InternetExchange(
            name="Wakanda-IX",
            slug="wakanda-ix",
        )
        i_x.tags = ["foo", "bar"]
        connection = Connection(
            ipv6_address="2001:db8:a::ffff",
            ipv4_address="192.0.2.128",
            internet_exchange_point=i_x,
        )
        group = BGPGroup(name="Transit Providers", slug="transit")
        group.tags = ["foo", "bar"]
        dps6 = DirectPeeringSession(
            local_autonomous_system=my_as,
            autonomous_system=a_s,
            ip_address="2001:db8::1",
            relationship=BGPRelationship.TRANSIT_PROVIDER,
        )
        dps6.tags = ["foo", "bar"]
        dps4 = DirectPeeringSession(
            local_autonomous_system=my_as,
            autonomous_system=a_s,
            ip_address="192.0.2.1",
            relationship=BGPRelationship.PRIVATE_PEERING,
        )
        dps4.tags = ["foo", "bar"]
        ixps6 = InternetExchangePeeringSession(
            autonomous_system=a_s,
            ixp_connection=connection,
            ip_address="2001:db8:a::aaaa",
        )
        ixps6.tags = ["foo", "bar"]
        ixps4 = InternetExchangePeeringSession(
            autonomous_system=a_s, ixp_connection=connection, ip_address="192.0.2.64"
        )
        ixps4.tags = ["foo", "bar"]

        return self.render(
            {
                "my_as": my_as,
                "autonomous_system": a_s,
                "internet_exchanges": [
                    {
                        "internet_exchange": i_x,
                        "sessions": [],
                        "missing_sessions": {
                            "ipv6": ["2001:db8:a::aaaa"],
                            "ipv4": ["192.0.2.64"],
                        },
                    }
                ],
                "direct_peering_sessions": [dps6, dps4],
            }
        )
