"""Unit display numbers (R15) and other model-level computed values and constraints."""

import datetime as dt

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from charters.models import TripUnit

# --- R15 unit display numbers -----------------------------------------------


@pytest.mark.django_db
def test_r15_single_bus_unit_shows_plain_number(make_contract, make_unit):
    unit = make_unit(make_contract(number=24817, bus_count=1))
    assert unit.display_number == "24817"


@pytest.mark.django_db
def test_r15_multi_bus_units_show_dash_number(make_contract, make_unit):
    c = make_contract(number=24823, bus_count=2)
    assert [make_unit(c, 1).display_number, make_unit(c, 2).display_number] == [
        "24823-1",
        "24823-2",
    ]


@pytest.mark.django_db
def test_r15_duplicate_shows_d_number(make_contract, make_unit):
    c = make_contract(number=24817, bus_count=1)
    make_unit(c, 1)
    assert make_unit(c, 1, is_duplicate=True).display_number == "24817-D1"
    assert make_unit(c, 2, is_duplicate=True).display_number == "24817-D2"


@pytest.mark.django_db
def test_r15_duplicate_on_multi_bus_contract(make_contract, make_unit):
    c = make_contract(number=24823, bus_count=2)
    assert make_unit(c, 1, is_duplicate=True).display_number == "24823-D1"


@pytest.mark.django_db
def test_r15_units_order_regular_then_duplicates(make_contract, make_unit):
    c = make_contract(number=24823, bus_count=2)
    make_unit(c, 1, is_duplicate=True)
    make_unit(c, 2)
    make_unit(c, 1)
    assert [u.display_number for u in c.units.all()] == ["24823-1", "24823-2", "24823-D1"]


@pytest.mark.django_db
def test_r15_regular_and_duplicate_can_share_unit_number(make_contract, make_unit):
    c = make_contract()
    make_unit(c, 1)
    make_unit(c, 1, is_duplicate=True)
    with pytest.raises(IntegrityError), transaction.atomic():
        make_unit(c, 1)


# --- Other computed values --------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("size", "needs_wc"),
    [("56-pax coach", False), ("56-pax coach WC", True), ("28-pax shuttle WC", True)],
)
def test_needs_wc_from_size_requirement(make_contract, size, needs_wc):
    assert make_contract(size_requirement=size).needs_wc is needs_wc


@pytest.mark.django_db
def test_is_multi_day(make_contract):
    assert make_contract().is_multi_day is False
    c = make_contract(number=24818, return_date=dt.date(2026, 11, 11))
    assert c.is_multi_day is True


# --- Ownership and constraints ----------------------------------------------


@pytest.mark.django_db
def test_unit_takes_owner_from_contract(make_contract, make_unit, owner):
    assert make_unit(make_contract()).owner == owner


@pytest.mark.django_db
def test_unit_owner_must_match_contract_owner(make_contract):
    other = get_user_model().objects.create_user(username="demo_other")
    unit = TripUnit(contract=make_contract(), owner=other, unit_number=1)
    with pytest.raises(ValidationError):
        unit.full_clean()


@pytest.mark.django_db
def test_contract_number_unique_per_owner_only(make_contract, terminal):
    make_contract(number=24817)
    with pytest.raises(IntegrityError), transaction.atomic():
        make_contract(number=24817)
    other = get_user_model().objects.create_user(username="demo_other")
    assert make_contract(owner=other, number=24817).number == 24817


@pytest.mark.django_db
@pytest.mark.parametrize("bus_count", [0, 21])
def test_bus_count_out_of_range_rejected(make_contract, bus_count):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_contract(bus_count=bus_count)


@pytest.mark.django_db
def test_zero_passengers_rejected(make_contract):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_contract(passengers=0)


@pytest.mark.django_db
def test_deleting_owner_deletes_contracts_and_units(make_contract, make_unit, owner):
    make_unit(make_contract())
    owner.delete()
    assert TripUnit.objects.count() == 0
