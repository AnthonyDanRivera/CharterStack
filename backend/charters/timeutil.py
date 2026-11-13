"""Visitor time zone handling.

The frontend sends its IANA time zone in an `X-Timezone` header (docs/API.md).
"Today" for seeding and the Reported / On location stamps use that zone.
"""

import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

DEFAULT_TZ_NAME = "America/New_York"


def resolve_timezone(name: str | None) -> ZoneInfo:
    """Return the named zone, or America/New_York when it is missing or unknown."""
    if name:
        try:
            return ZoneInfo(name.strip())
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return ZoneInfo(DEFAULT_TZ_NAME)


def request_timezone(request) -> ZoneInfo:
    return resolve_timezone(request.headers.get("X-Timezone"))


def today_in(tz: ZoneInfo) -> dt.date:
    return timezone.now().astimezone(tz).date()
