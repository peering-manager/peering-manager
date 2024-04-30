from django.conf import settings
from django_rq.management.commands.rqworker import Command as BuiltinCommand


class Command(BuiltinCommand):
    """
    Subclass django_rq's built-in rqworker to listen on all configured queues if none
    are specified (instead of only the 'default' queue).
    """

    def handle(self, *args, **options):
        if len(args) < 1:
            args = settings.RQ_QUEUES

        super().handle(*args, **options)
