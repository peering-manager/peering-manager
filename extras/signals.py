import random
from datetime import timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import JobResult


@receiver(post_save, sender=JobResult)
def cleanup_old_job_results(sender, instance, **kwargs):
    if settings.CHANGELOG_RETENTION and random.randint(1, 1000) == 1:
        date_limit = timezone.now() - timedelta(days=settings.CHANGELOG_RETENTION)
        JobResult.objects.filter(created__lt=date_limit).delete()
