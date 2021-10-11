from django.core.management.base import BaseCommand

from net.models import Connection
from peering.models import InternetExchange


class Command(BaseCommand):
    help = "Import existing sessions from Internet Exchanges."

    def handle(self, *args, **options):
        self.stdout.write("[*] Importing existing sessions from IXPs")
        internet_exchanges = InternetExchange.objects.all()

        for ix in internet_exchanges:
            if options["verbosity"] >= 2:
                self.stdout.write(f"[*] Attempting to import sessions for {ix}")
            connections = Connection.objects.filter(
                internet_exchange_point=ix,
            )
            if connections.count() < 1:
                if options["verbosity"] >= 2:
                    self.stdout.write(f"  - No connections on {ix}")
                continue

            for connection in connections:
                if not connection.router or not connection.router.is_usable_for_task():
                    if options["verbosity"] >= 2:
                        self.stdout.write(
                            f"  - Ignored connection {connection}, no router associated or router is not usable"
                        )
                    continue

                session_number, asn_number = ix.import_sessions(connection)
                self.stdout.write(
                    f"[*] Imported {session_number} sessions for {asn_number} autonomous systems"
                )
