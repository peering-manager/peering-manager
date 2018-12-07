import logging

from django.core.management.base import BaseCommand

from peeringdb.api import PeeringDB


class Command(BaseCommand):
    help = "Index peer records based on PeeringDB."
    logger = logging.getLogger("peering.manager.peeringdb")

    def handle(self, *args, **options):
        self.logger.info("Indexing peer records...")

        api = PeeringDB()
        api.force_peer_records_discovery()
