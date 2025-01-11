import datetime
from zoneinfo import ZoneInfo

from django.conf import settings

__all__ = ("FUNCTION_DICT",)


def time_now(format: str = "%Y-%m-%dT%H:%M:%SZ", timezone: str = "") -> str:
    """
    Return a date and time based on a given format, default to ISO8601 as per RFC3339.

    https://www.rfc-editor.org/rfc/rfc3339
    """
    tz = ZoneInfo(key=timezone or settings.TIME_ZONE)
    return datetime.datetime.now(tz=tz).strftime(format=format)


FUNCTION_DICT = {"now": time_now}
