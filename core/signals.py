from django.dispatch import Signal

__all__ = ("post_synchronisation", "pre_synchronisation")

post_synchronisation = Signal()
pre_synchronisation = Signal()
