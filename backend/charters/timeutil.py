"""Visitor time zone handling.

The frontend sends its IANA time zone in an `X-Timezone` header (docs/API.md).
"Today" for seeding and the Reported / On location stamps use that zone.
"""

import datetime as dt
import re
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


_ONE_WAY = {"OW", "ONE WAY", "ONEWAY"}
_AMPM_RE = re.compile(r"\s?(AM|PM|A|P)$")


def parse_loose_time(text: str, allow_one_way: bool = False) -> dt.time | None:
    """R02: normalize loosely typed times to a `time` (shown as 24-hour HH:MM).

    `7`/`07` -> 07:00, `730`/`0730`/`7:30` -> 07:30, `1915` -> 19:15,
    `7p`/`7 pm`/`7:30PM` -> 19:00/19:00/19:30. `ow` or `one way` returns None
    (One way) when `allow_one_way`. Anything else raises ValueError.
    """
    t = re.sub(r"\s+", " ", str(text).strip().upper().replace(".", ""))
    if not t:
        raise ValueError("Enter a valid time")
    if t in _ONE_WAY:
        if allow_one_way:
            return None
        raise ValueError("Enter a valid time")

    meridiem = None
    m = _AMPM_RE.search(t)
    if m:
        meridiem = m.group(1)[0]
        t = t[: m.start()].strip()

    if re.fullmatch(r"\d{1,2}:\d{1,2}", t):
        hour, minute = (int(p) for p in t.split(":"))
    elif re.fullmatch(r"\d{3,4}", t):
        hour, minute = int(t[:-2]), int(t[-2:])
    elif re.fullmatch(r"\d{1,2}", t):
        hour, minute = int(t), 0
    else:
        raise ValueError("Enter a valid time")

    if minute > 59:
        raise ValueError("Enter a valid time")
    if meridiem:
        if not 1 <= hour <= 12:
            raise ValueError("Enter a valid time")
        hour = hour % 12 + (12 if meridiem == "P" else 0)
    if hour > 23:
        raise ValueError("Enter a valid time")
    return dt.time(hour, minute)


def format_hhmm(value: dt.time | None) -> str | None:
    """R01: 24-hour `HH:MM`, never AM/PM."""
    return value.strftime("%H:%M") if value is not None else None
