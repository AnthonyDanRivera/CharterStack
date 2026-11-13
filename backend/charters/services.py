"""Multi-step business logic. Views, serializers and commands call into here."""

import datetime as dt
import hashlib
import hmac
import json
import re
import secrets
import string
from decimal import Decimal
from functools import cache
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.utils import timezone

from .models import Bus, Contract, DemoSession, Driver, Terminal, TripUnit, ZipCode
from .timeutil import today_in

DEMO_USERNAME_PREFIX = "demo_"
_ID_ALPHABET = string.ascii_lowercase + string.digits


@cache
def load_seed() -> dict[str, Any]:
    """Read `seed/seed_demo.json` once per process."""
    with open(settings.SEED_FILE, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------


@transaction.atomic
def seed_reference(data: dict[str, Any] | None = None) -> dict[str, int]:
    """Load terminals, drivers, buses and ZIP codes from the seed. Idempotent.

    Rows are matched on their natural key (code, name, number, zip) and updated in
    place, so running it again never duplicates rows and never touches sandboxes.
    Returns how many rows of each kind are in the seed.
    """
    data = data if data is not None else load_seed()

    for t in data["terminals"]:
        Terminal.objects.update_or_create(code=t["code"], defaults={"name": t["name"]})
    for d in data["drivers"]:
        Driver.objects.update_or_create(name=d["name"], defaults={"phone": d["phone"]})
    for b in data["buses"]:
        Bus.objects.update_or_create(
            number=b["number"],
            defaults={
                "seats": b["seats"],
                "model": b["model"],
                "has_wc_lift": b.get("has_wc_lift", False),
            },
        )
    for zip_code, (city, state, county) in data["zip_lookup"].items():
        ZipCode.objects.update_or_create(
            zip=zip_code, defaults={"city": city, "state": state, "county": county}
        )

    return {
        "terminals": len(data["terminals"]),
        "drivers": len(data["drivers"]),
        "buses": len(data["buses"]),
        "zip_codes": len(data["zip_lookup"]),
    }


# ---------------------------------------------------------------------------
# Demo login and sandbox seeding (docs/DEMO_SANDBOX.md)
# ---------------------------------------------------------------------------


def hash_ip(ip: str | None) -> str:
    """Keyed hash of the visitor's IP, so we can spot abuse without storing the IP."""
    if not ip:
        return ""
    return hmac.new(settings.SECRET_KEY.encode(), ip.encode(), hashlib.sha256).hexdigest()


def _new_demo_suffix() -> str:
    User = get_user_model()
    while True:
        suffix = "".join(secrets.choice(_ID_ALPHABET) for _ in range(5))
        if not User.objects.filter(username=DEMO_USERNAME_PREFIX + suffix).exists():
            return suffix


@transaction.atomic
def create_demo_session(ip: str | None, tz: ZoneInfo) -> DemoSession:
    """Create a throwaway demo user, its DemoSession and a seeded sandbox.

    The user has an unusable password and no staff rights, so it can only be used
    through the session cookie set at demo login.
    """
    suffix = _new_demo_suffix()
    user = get_user_model().objects.create_user(username=DEMO_USERNAME_PREFIX + suffix)
    demo = DemoSession.objects.create(
        user=user, short_id=f"DEMO-{suffix.upper()}", ip_hash=hash_ip(ip)
    )
    seed_sandbox(user, today=today_in(tz), tz=tz)
    return demo


_TEXT_DATE_RE = re.compile(r"\b(?:(Mon|Tue|Wed|Thu|Fri|Sat|Sun) )?(\d{2})/(\d{2})\b")


def shift_text_dates(text: str, base: dt.date, days: int) -> str:
    """Shift `MM/DD` dates (with an optional weekday, `Mon 11/09`) inside free text.

    Seed itineraries and notes mention dates; without this they would disagree
    with the shifted trip dates. The year is taken as the one nearest the base day.
    """
    if not days or not text:
        return text

    def replace(match: re.Match) -> str:
        weekday, month, day = match.group(1), int(match.group(2)), int(match.group(3))
        candidates = []
        for year in (base.year - 1, base.year, base.year + 1):
            try:
                candidates.append(dt.date(year, month, day))
            except ValueError:
                pass
        if not candidates:
            return match.group(0)
        original = min(candidates, key=lambda d: abs((d - base).days))
        shifted = original + dt.timedelta(days=days)
        out = f"{shifted:%m/%d}"
        return f"{shifted:%a} {out}" if weekday else out

    return _TEXT_DATE_RE.sub(replace, text)


def _time(value: str | None) -> dt.time | None:
    return dt.time.fromisoformat(value) if value else None


@transaction.atomic
def seed_sandbox(
    user: AbstractBaseUser,
    today: dt.date,
    tz: ZoneInfo,
    data: dict[str, Any] | None = None,
) -> list[Contract]:
    """Copy the sample contracts into `user`'s sandbox, dated around `today`.

    Every date moves by the same number of days so the seed's `base_date` becomes
    `today`. Each contract gets `bus_count` regular units; the seed's dispatch data
    (`unit1`) goes on unit 1 and other units start blank. Confirmation timestamps
    are read as local times in `tz` and shift by the same days.
    """
    data = data if data is not None else load_seed()
    if not Terminal.objects.exists():
        seed_reference(data)

    base = dt.date.fromisoformat(data["base_date"])
    shift = dt.timedelta(days=(today - base).days)
    terminals = {t.code: t for t in Terminal.objects.all()}
    drivers = {d.name: d for d in Driver.objects.all()}
    buses = {b.number: b for b in Bus.objects.all()}
    zips = data["zip_lookup"]

    def county(zip_code: str) -> str:
        return zips[zip_code][2] if zip_code in zips else ""

    contracts: list[Contract] = []
    for row in data["contracts"]:
        contracts.append(
            Contract(
                owner=user,
                number=row["number"],
                status=row["status"],
                organization=row["organization"],
                group_name=row["group_name"],
                passengers=row["passengers"],
                contact_name=row["contact_name"],
                contact_phone=row["contact_phone"],
                begin_date=dt.date.fromisoformat(row["begin_date"]) + shift,
                spot_time=_time(row["spot_time"]),
                start_time=_time(row["start_time"]),
                return_date=dt.date.fromisoformat(row["return_date"]) + shift,
                return_time=_time(row["return_time"]),
                pickup_location=row["pickup_location"],
                pickup_address=row["pickup_address"],
                pickup_city=row["pickup_city"],
                pickup_state=row["pickup_state"],
                pickup_zip=row["pickup_zip"],
                pickup_county=county(row["pickup_zip"]),
                dest_location=row["dest_location"],
                dest_address=row["dest_address"],
                dest_city=row["dest_city"],
                dest_state=row["dest_state"],
                dest_zip=row["dest_zip"],
                dest_county=county(row["dest_zip"]),
                itinerary=shift_text_dates(row["itinerary"], base, shift.days),
                bus_count=row["bus_count"],
                terminal=terminals[row["terminal"]],
                size_requirement=row["size_requirement"],
                requested_driver=drivers.get(row["requested_driver"] or ""),
                info=shift_text_dates(row["info"], base, shift.days),
                total_price=Decimal(str(row["total_price"])),
                deposit_required=Decimal(str(row["deposit_required"])),
                total_paid=Decimal(str(row["total_paid"])),
            )
        )
    Contract.objects.bulk_create(contracts)

    units: list[TripUnit] = []
    for contract, row in zip(contracts, data["contracts"], strict=True):
        seeded = row.get("unit1") or {}
        confirmed_at = None
        if seeded.get("confirmed_at"):
            local = dt.datetime.fromisoformat(seeded["confirmed_at"]) + shift
            confirmed_at = local.replace(tzinfo=tz)
        for n in range(1, contract.bus_count + 1):
            unit = TripUnit(owner=user, contract=contract, unit_number=n)
            if n == 1:
                unit.driver = drivers.get(seeded.get("driver") or "")
                unit.bus = buses.get(seeded.get("bus") or "")
                unit.report_time = _time(seeded.get("report_time"))
                unit.confirm_initials = seeded.get("confirm_initials") or ""
                unit.confirmed_at = confirmed_at
            units.append(unit)
    TripUnit.objects.bulk_create(units)
    return contracts


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


def cleanup_demo(now: dt.datetime | None = None) -> int:
    """Delete demo users whose sandbox is older than DEMO_SANDBOX_HOURS.

    Selects strictly by the `demo_` username prefix AND an existing DemoSession
    (never superusers or staff). Contracts, units and the DemoSession go with the
    user through on_delete=CASCADE. Returns the number of users deleted.
    """
    now = now or timezone.now()
    cutoff = now - dt.timedelta(hours=settings.DEMO_SANDBOX_HOURS)
    expired = get_user_model().objects.filter(
        username__startswith=DEMO_USERNAME_PREFIX,
        demo_session__isnull=False,
        demo_session__created_at__lt=cutoff,
        is_superuser=False,
        is_staff=False,
    )
    count = expired.count()
    expired.delete()
    return count
