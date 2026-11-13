import datetime as dt
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from charters.models import Contract, Terminal, TripUnit


@pytest.fixture
def owner(db):
    return get_user_model().objects.create_user(username="demo_test1")


@pytest.fixture
def terminal(db):
    return Terminal.objects.create(code="NJ", name="New Jersey")


@pytest.fixture
def make_contract(owner, terminal):
    """Build and save a valid contract; override any field with keyword arguments."""

    def _make(**overrides) -> Contract:
        fields = {
            "owner": owner,
            "number": 24817,
            "organization": "Union City Public Schools",
            "group_name": "9th Grade Biology",
            "passengers": 48,
            "contact_name": "Ms. Alicia Gomez",
            "contact_phone": "(201) 555-0117",
            "begin_date": dt.date(2026, 11, 9),
            "spot_time": dt.time(6, 45),
            "start_time": dt.time(7, 15),
            "return_date": dt.date(2026, 11, 9),
            "return_time": dt.time(14, 15),
            "pickup_address": "2500 Kennedy Blvd",
            "pickup_city": "Union City",
            "pickup_state": "NJ",
            "dest_address": "222 Jersey City Blvd",
            "dest_city": "Jersey City",
            "dest_state": "NJ",
            "terminal": terminal,
            "size_requirement": "56-pax coach",
            "total_price": Decimal("950.00"),
        }
        fields.update(overrides)
        return Contract.objects.create(**fields)

    return _make


@pytest.fixture
def make_unit():
    def _make(contract: Contract, unit_number: int = 1, is_duplicate: bool = False) -> TripUnit:
        return TripUnit.objects.create(
            contract=contract, unit_number=unit_number, is_duplicate=is_duplicate
        )

    return _make


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Throttle counters live in the cache; reset them so tests don't throttle each other."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def reference(db):
    from charters.services import seed_reference

    seed_reference()


@pytest.fixture
def demo_client(reference):
    """Return a factory: each call gives a fresh browser logged into its own sandbox."""
    from django.test import Client

    def _make(**headers) -> Client:
        client = Client(headers=headers)
        response = client.post("/api/demo-login/")
        assert response.status_code == 201, response.content
        return client

    return _make
