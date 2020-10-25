import logging
import peering.models

from argparse import Action
from django.conf import settings
from django.core.management.base import BaseCommand
from utils.models import SoftDeleteModel


class MinAgeAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 0:
            parser.error(f"Minimum age for {option_string} is 0")

        setattr(namespace, self.dest, values)


class Command(BaseCommand):
    help = "Purge soft deleted objects that are older than a certain age"
    logger = logging.getLogger("peering.manager.peering")

    def add_arguments(self, parser):
        parser.add_argument(
            "--age",
            type=int,
            action=MinAgeAction,
            required=True,
            default=settings.SOFTDELETE_RETENTION,
            help=f"Minimum age to purge in days (>=0) [default={settings.SOFTDELETE_RETENTION}]",
        )

    def handle(self, *args, **options):
        self.logger.info(f"Purging objects at least {options['age']} days old")
        SoftDeleteModel.purge_deleted(peering.models, options["age"])
