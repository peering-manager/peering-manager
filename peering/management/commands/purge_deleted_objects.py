from datetime import timedelta
import logging
import inspect
import datetime
import pytz
import peering.models

from peering_manager import settings
from argparse import Action
from django.core.management.base import BaseCommand
from utils.models import SoftDeleteModel
from safedelete import HARD_DELETE

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
            help="Minimum age to purge in days (>=0)",
        )

    def handle(self, *args, **options):
        self.logger.info(f"Purging objects at least {options['age']} days old")       
        now = datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
        expiry_date = now - datetime.timedelta(days=options['age'])
        self.logger.info(f"Objects deleted before {expiry_date} will be purged")
        model_classes = [x[1] for x in inspect.getmembers(peering.models, inspect.isclass) if issubclass(x[1], SoftDeleteModel) and not x[1]._meta.abstract ]
        for model in model_classes:
            count, _ = model.deleted_objects.filter(deleted__lte=expiry_date).delete(HARD_DELETE)
            self.logger.info(f"Purged {count} {model._meta.verbose_name} objects")
            