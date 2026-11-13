"""Multi-step business logic. Views, serializers and commands call into here."""

import json
from functools import cache
from typing import Any

from django.conf import settings
from django.db import transaction

from .models import Bus, Driver, Terminal, ZipCode


@cache
def load_seed() -> dict[str, Any]:
    """Read `seed/seed_demo.json` once per process."""
    with open(settings.SEED_FILE, encoding="utf-8") as fh:
        return json.load(fh)


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
