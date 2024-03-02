from django.dispatch import Signal, receiver

__all__ = ("post_synchronisation", "pre_synchronisation")

post_synchronisation = Signal()
pre_synchronisation = Signal()


@receiver(post_synchronisation)
def auto_synchronisation(instance, **kwargs):
    """
    Synchronise `DataFile`s with `AutoSynchronisationRecord`s after synchronising a
    `DataSource`.
    """
    from .models import AutoSynchronisationRecord

    for record in AutoSynchronisationRecord.objects.filter(
        data_file__source=instance
    ).prefetch_related("object"):
        record.object.synchronise(save=True)
