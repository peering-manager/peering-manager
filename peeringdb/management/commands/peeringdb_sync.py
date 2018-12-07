import logging

from django.core.management.base import BaseCommand

from peeringdb.api import PeeringDB


class Command(BaseCommand):
    help = "Sync known networks of PeeringDB."
    logger = logging.getLogger("peering.manager.peeringdb")

    def handle(self, *args, **options):
        self.logger.info("Syncing networks with PeeringDB...")

        api = PeeringDB()
        api.update_local_database(api.get_last_sync_time())
