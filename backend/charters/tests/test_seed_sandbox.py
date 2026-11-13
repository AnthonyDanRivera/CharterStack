"""seed_sandbox(): 12 contracts, 13 units, dated around today (docs/DEMO_SANDBOX.md)."""

import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model

from charters.models import Contract, Terminal, TripUnit
from charters.services import seed_sandbox, shift_text_dates
from charters.timeutil import today_in

NY = ZoneInfo("America/New_York")
TODAY = dt.date(2026, 11, 12)  # base day in the seed is Mon 2026-11-09, so +3 days


@pytest.fixture
def sandbox(reference):
    user = get_user_model().objects.create_user(username="demo_seed1")
    seed_sandbox(user, today=TODAY, tz=NY)
    contracts = {c.number: c for c in Contract.objects.filter(owner=user)}
    return user, contracts


def test_sandbox_has_12_contracts_and_13_units(sandbox):
    user, contracts = sandbox
    assert len(contracts) == 12
    assert TripUnit.objects.filter(owner=user).count() == 13
    assert TripUnit.objects.exclude(owner=user).count() == 0


def test_base_day_becomes_today(sandbox):
    _, c = sandbox
    assert c[24811].begin_date == TODAY
    assert c[24826].begin_date == TODAY + dt.timedelta(days=1)
    # Multi-day trip keeps its length.
    assert (c[24838].begin_date, c[24838].return_date) == (
        dt.date(2026, 11, 14),
        dt.date(2026, 11, 17),
    )


def test_times_money_and_status_copied(sandbox):
    _, c = sandbox
    assert (c[24811].spot_time, c[24811].start_time) == (dt.time(5, 0), dt.time(5, 30))
    assert c[24811].payment_status == "Paid in full"
    assert c[24841].status == "quote"
    assert c[24844].status == "cancelled"
    assert c[24811].terminal.code == "NJ"
    assert c[24811].requested_driver.name == "Marcus Bell"
    assert c[24817].requested_driver is None


def test_counties_filled_from_zip_lookup(sandbox):
    _, c = sandbox
    assert (c[24811].pickup_county, c[24811].dest_county) == ("Hudson County", "Lehigh County")
    assert c[24841].dest_county == ""  # 18042 is not in the lookup


def test_unit1_gets_seeded_dispatch_data(sandbox):
    _, c = sandbox
    unit = c[24811].units.get()
    assert unit.driver.name == "Marcus Bell"
    assert unit.bus.number == "4512"
    assert unit.report_time == dt.time(4, 15)
    assert unit.confirm_initials == "AR"
    # 2026-11-04 10:12 New York, shifted by 3 days.
    assert unit.confirmed_at == dt.datetime(2026, 11, 7, 10, 12, tzinfo=NY)


def test_multi_bus_contract_unit2_starts_blank(sandbox):
    _, c = sandbox
    u1, u2 = c[24823].units.all()
    assert [u1.display_number, u2.display_number] == ["24823-1", "24823-2"]
    assert u1.driver.name == "Luis Ortega"
    assert u1.report_time == dt.time(10, 0)
    assert (u2.driver, u2.bus, u2.report_time, u2.confirm_initials) == (None, None, None, "")


def test_dates_in_itinerary_and_info_shift_too(sandbox):
    _, c = sandbox
    assert c[24811].itinerary.startswith("Thu 11/12  05:30  Depart")
    assert "Mon 11/09" not in c[24811].itinerary
    assert c[24838].itinerary.splitlines()[-1].startswith("Tue 11/17  18:00")
    assert c[24844].info == "Cancelled by customer 11/11; deposit kept per policy."
    assert c[24841].info == "Customer is comparing quotes; follow up by 11/19."


def test_seeding_on_base_day_changes_nothing(reference):
    user = get_user_model().objects.create_user(username="demo_seed2")
    seed_sandbox(user, today=dt.date(2026, 11, 9), tz=NY)
    c = Contract.objects.get(owner=user, number=24811)
    assert c.begin_date == dt.date(2026, 11, 9)
    assert c.itinerary.startswith("Mon 11/09")


@pytest.mark.parametrize(
    ("text", "base", "days", "expected"),
    [
        ("Mon 11/09  05:30", dt.date(2026, 11, 9), 3, "Thu 11/12  05:30"),
        ("Wed 12/30 depart", dt.date(2026, 12, 30), 5, "Mon 01/04 depart"),
        ("by 01/02", dt.date(2026, 12, 30), 1, "by 01/03"),  # 01/02 read as next year
        ("Ceremony at 11 AM; I-95", dt.date(2026, 11, 9), 3, "Ceremony at 11 AM; I-95"),
        ("13/45 is not a date", dt.date(2026, 11, 9), 3, "13/45 is not a date"),
    ],
)
def test_shift_text_dates(text, base, days, expected):
    assert shift_text_dates(text, base, days) == expected


@pytest.mark.django_db
def test_seed_sandbox_loads_reference_data_if_missing():
    user = get_user_model().objects.create_user(username="demo_seed3")
    seed_sandbox(user, today=TODAY, tz=NY)
    assert Terminal.objects.count() == 5


@pytest.mark.django_db
@pytest.mark.parametrize("tz_name", ["Pacific/Kiritimati", "Pacific/Pago_Pago"])
def test_demo_login_dates_sandbox_on_visitors_today(demo_client, tz_name):
    """UTC+14 and UTC-11 are always on different dates; each gets its own today."""
    demo_client(**{"X-Timezone": tz_name})
    contract = Contract.objects.get(number=24811)
    assert contract.begin_date == today_in(ZoneInfo(tz_name))
