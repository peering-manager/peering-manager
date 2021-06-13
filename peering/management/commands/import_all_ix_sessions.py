import logging

from django.core.management.base import BaseCommand

from net.models import Connection
from peering.models import InternetExchange


class Command(BaseCommand):
    help = "Import existing sessions from Internet Exchanges."
    logger = logging.getLogger("peering.manager.peering")

    def handle(self, *args, **options):
        self.logger.info("Importing existing sessions from Internet Exchanges...")
        internet_exchanges = InternetExchange.objects.all()

        for ix in internet_exchanges:
            self.logger.info(f"Attempting to import sessions for {ix}")
            connections = Connection.objects.filter(
                internet_exchange_point=ix,
            )
            if connections.count() < 1:
                self.logger.info(f"No Connections on {ix}")
                continue

            for connection in connections:
                if not connection.router or not connection.router.is_usable_for_task():
                    self.logger.info(
                        f"Ignored connection {connection}, no router associated or router is not usable."
                    )
                    continue

                session_number, asn_number = ix.import_sessions(connection)
                self.logger.info(
                    f"Imported {session_number} sessions for {asn_number} autonomous systems."
                )
