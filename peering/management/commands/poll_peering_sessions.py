from django.core.management.base import BaseCommand

from peering.models import BGPGroup, InternetExchange


class Command(BaseCommand):
    help = "Poll peering sessions for BGP groups and Internet Exchanges."

    def add_arguments(self, parser):
        parser.add_argument(
            "-a", "--all", action="store_true", help="Poll all peering sessions"
        )
        parser.add_argument(
            "-g",
            "--bgp-groups",
            action="store_true",
            help="Poll peering sessions for BGP groups only",
        )
        parser.add_argument(
            "-i",
            "--internet-exchanges",
            action="store_true",
            help="Poll peering sessions for Internet Exchanges only",
        )

    def handle(self, *args, **options):
        if options["all"] or options["bgp_groups"]:
            self.stdout.write("[*] Polling peering sessions for BGP groups")
            bgp_groups = BGPGroup.objects.all()
            for bgp_group in bgp_groups:
                bgp_group.poll_peering_sessions()

        if options["all"] or options["internet_exchanges"]:
            self.stdout.write("[*] Polling peering sessions for Internet Exchanges")
            internet_exchanges = InternetExchange.objects.all()
            for internet_exchange in internet_exchanges:
                internet_exchange.poll_peering_sessions()
