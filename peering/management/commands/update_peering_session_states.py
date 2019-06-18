import logging

from django.core.management.base import BaseCommand

from peering.models import InternetExchange


class Command(BaseCommand):
    help = "[DEPRECATED] Update peering session states for Internet Exchanges."
    logger = logging.getLogger("peering.manager.peering")

    def handle(self, *args, **options):
        self.logger.info("[DEPRECATED] Updating peering session states...")

        internet_exchanges = InternetExchange.objects.all()
        for internet_exchange in internet_exchanges:
            internet_exchange.poll_peering_sessions()
