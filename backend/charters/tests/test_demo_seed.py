"""Guards for seed/seed_demo.json, the generated data every demo visitor gets.

Other tests use the small fixed seed_test.json; these load the real demo seed
and check it stays realistic and valid as seed/generate_demo.py changes.
"""

import datetime as dt
import math
from collections import defaultdict
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from charters.api.serializers import ContractSerializer
from charters.board import BoardQuery, build_board
from charters.models import Bus, Contract, TripUnit
from charters.services import load_seed, seed_sandbox

NY = ZoneInfo("America/New_York")
TODAY = dt.date(2026, 11, 13)


@pytest.fixture
def demo_seed(settings):
    settings.SEED_FILE = settings.BASE_DIR.parent / "seed" / "seed_demo.json"
    load_seed.cache_clear()
    yield load_seed()
    load_seed.cache_clear()


@pytest.fixture
def sandbox(db, demo_seed):
    user = get_user_model().objects.create_user(username="demo_seedcheck")
    seed_sandbox(user, today=TODAY, tz=NY)
    return user


def test_demo_seed_is_bigger_than_the_test_seed(demo_seed):
    assert 45 <= len(demo_seed["contracts"]) <= 70
    assert len(demo_seed["buses"]) >= 30
    assert len(demo_seed["drivers"]) >= 25
    assert all(b.get("terminal") for b in demo_seed["buses"])


def test_every_demo_contract_passes_booking_validation(sandbox):
    request = APIRequestFactory().post("/api/contracts/")
    request.user = sandbox
    for c in Contract.objects.filter(owner=sandbox):
        data = ContractSerializer(c, context={"request": request}).data
        body = {k: v for k, v in data.items() if k not in {"id", "number", "units"}}
        check = ContractSerializer(c, data=body, partial=False, context={"request": request})
        assert check.is_valid(), (c.number, check.errors)


def test_no_driver_or_bus_double_booked(sandbox):
    drivers: dict[tuple[int, dt.date], int] = defaultdict(int)
    buses: dict[tuple[int, dt.date], int] = defaultdict(int)
    for u in TripUnit.objects.filter(owner=sandbox).select_related("contract"):
        c = u.contract
        if c.status == "quote":
            continue
        for n in range((c.return_date - c.begin_date).days + 1):
            day = c.begin_date + dt.timedelta(n)
            if u.driver_id:
                drivers[(u.driver_id, day)] += 1
            if u.bus_id:
                buses[(u.bus_id, day)] += 1
    assert max(drivers.values()) == 1
    assert max(buses.values()) == 1


def test_generated_buses_come_from_the_terminal_and_fit(sandbox, demo_seed):
    hand_written = {c["number"] for c in demo_seed["contracts"][:12]}
    units = TripUnit.objects.filter(owner=sandbox, bus__isnull=False).select_related(
        "contract", "bus", "contract__terminal", "bus__terminal"
    )
    for u in units.exclude(contract__number__in=hand_written):
        c = u.contract
        assert u.bus.terminal_id == c.terminal_id, c.number
        assert u.bus.seats >= math.ceil(c.passengers / c.bus_count), c.number
        if c.needs_wc:
            assert u.bus.has_wc_lift, c.number


def test_todays_board_looks_like_a_real_day(sandbox):
    board = build_board(TripUnit.objects.filter(owner=sandbox), BoardQuery(start=TODAY, end=TODAY))
    assert 20 <= board["counts"]["trips"] <= 25
    assert 3 <= board["counts"]["need_driver_or_bus"] <= 8
    assert board["counts"]["pending_confirmation"] >= 3
    terminals = {r["terminal"] for r in board["rows"]}
    assert len(terminals) >= 3


def test_demo_fleet_loads_with_terminals(sandbox):
    assert Bus.objects.filter(terminal__isnull=True).count() == 0
    assert set(Bus.objects.values_list("terminal__code", flat=True)) == {
        "NJ",
        "NY",
        "PA",
        "CT",
        "MA",
    }
