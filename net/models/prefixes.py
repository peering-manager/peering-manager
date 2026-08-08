from django.db import models
from django.db.models.functions import Coalesce
from netfields import CidrAddressField, NetManager

__all__ = ("PrefixListEntry",)


class PrefixListEntry(models.Model):
    """
    A single IRR-derived prefix-list entry as produced by bgpq3/bgpq4.

    Entries are deduplicated and shared between autonomous systems link table. This is derived data (a cache of IRR
    lookups), hence no change logging or any other features.
    """

    prefix = CidrAddressField()
    exact = models.BooleanField(default=False)
    greater_equal = models.PositiveSmallIntegerField(blank=True, null=True)
    less_equal = models.PositiveSmallIntegerField(blank=True, null=True)

    objects = NetManager()

    class Meta:
        ordering = ("prefix",)
        verbose_name = "IRR prefix"
        verbose_name_plural = "IRR prefixes"
        constraints = [
            # NULL values compare as distinct in a plain unique constraint, so coalesce the optional bounds to make
            # (prefix, exact, ge, le) truly unique
            models.UniqueConstraint(
                models.F("prefix"),
                models.F("exact"),
                Coalesce("greater_equal", 0),
                Coalesce("less_equal", 0),
                name="net_prefixlistentry_unique",
            )
        ]

    def __str__(self) -> str:
        text = str(self.prefix)
        if self.exact:
            return f"{text} exact"
        if self.greater_equal is not None:
            text += f" ge {self.greater_equal}"
        if self.less_equal is not None:
            text += f" le {self.less_equal}"
        return text
