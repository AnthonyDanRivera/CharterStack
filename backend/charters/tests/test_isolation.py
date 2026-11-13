"""Sandbox isolation (docs/DEMO_SANDBOX.md, CLAUDE.md rule 1).

Two visitors, A and B, each with a seeded sandbox. A must never see or change B's
rows, and B's IDs must look exactly like IDs that do not exist (404, never 403).

Phase 2 tests the OwnedModelViewSet base class through test-only endpoints
(`isolation_urls.py`). When the real contract and unit endpoints arrive, add
them to the parametrized lists at the bottom of this file.
"""

import pytest

from charters.models import Contract, TripUnit
from charters.services import create_demo_session
from charters.timeutil import resolve_timezone

pytestmark = [pytest.mark.django_db, pytest.mark.urls("charters.tests.isolation_urls")]


@pytest.fixture
def a_and_b(demo_client):
    a = demo_client()
    b = demo_client()
    a_user = a.session["_auth_user_id"]
    b_user = b.session["_auth_user_id"]
    return a, a_user, b, b_user


@pytest.fixture
def b_rows(a_and_b):
    _, _, _, b_user = a_and_b
    contract = Contract.objects.filter(owner_id=b_user).first()
    unit = TripUnit.objects.filter(owner_id=b_user).first()
    return contract, unit


def test_list_endpoints_only_show_own_rows(a_and_b):
    a, a_user, _, b_user = a_and_b
    for url, model in [("/t/contracts/", Contract), ("/t/units/", TripUnit)]:
        ids = {row["id"] for row in a.get(url).json()}
        assert ids == set(model.objects.filter(owner_id=a_user).values_list("id", flat=True))
        assert not ids & set(model.objects.filter(owner_id=b_user).values_list("id", flat=True))


@pytest.mark.parametrize("method", ["get", "patch", "put", "delete"])
@pytest.mark.parametrize("kind", ["contracts", "units"])
def test_other_owners_rows_return_404(a_and_b, b_rows, method, kind):
    a, _, _, _ = a_and_b
    contract, unit = b_rows
    pk = contract.pk if kind == "contracts" else unit.pk
    response = getattr(a, method)(
        f"/t/{kind}/{pk}/", data={"dispatch_notes": "x"}, content_type="application/json"
    )
    assert response.status_code == 404


def test_other_owners_404_matches_missing_id(a_and_b, b_rows):
    a, _, _, _ = a_and_b
    _, unit = b_rows
    missing = a.get("/t/units/999999/")
    others = a.get(f"/t/units/{unit.pk}/")
    assert (missing.status_code, others.status_code) == (404, 404)
    assert others.json() == missing.json()


def test_action_on_other_owners_unit_returns_404(a_and_b, b_rows):
    a, _, _, _ = a_and_b
    _, unit = b_rows
    assert a.post(f"/t/units/{unit.pk}/duplicate/").status_code == 404
    assert not TripUnit.objects.filter(contract=unit.contract, is_duplicate=True).exists()


def test_b_rows_unchanged_after_a_tries(a_and_b, b_rows):
    a, _, _, _ = a_and_b
    contract, unit = b_rows
    a.patch(f"/t/units/{unit.pk}/", {"dispatch_notes": "hacked"}, content_type="application/json")
    a.delete(f"/t/contracts/{contract.pk}/")
    unit.refresh_from_db()
    assert unit.dispatch_notes == ""
    assert Contract.objects.filter(pk=contract.pk).exists()


def test_cannot_create_unit_on_other_owners_contract(a_and_b, b_rows):
    a, _, _, _ = a_and_b
    contract, _ = b_rows
    response = a.post(
        "/t/units/",
        {"contract": contract.pk, "unit_number": 9, "is_duplicate": True},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "contract" in response.json()
    assert contract.units.count() == 1


def test_create_sets_owner_to_request_user(a_and_b):
    a, a_user, _, _ = a_and_b
    own_contract = Contract.objects.filter(owner_id=a_user).first()
    response = a.post(
        "/t/units/",
        {"contract": own_contract.pk, "unit_number": 9, "is_duplicate": True},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert TripUnit.objects.get(pk=response.json()["id"]).owner_id == int(a_user)


def test_owner_in_body_is_ignored(a_and_b):
    a, a_user, _, b_user = a_and_b
    own_contract = Contract.objects.filter(owner_id=a_user).first()
    a.patch(
        f"/t/contracts/{own_contract.pk}/",
        {"owner": int(b_user), "organization": "Renamed"},
        content_type="application/json",
    )
    own_contract.refresh_from_db()
    assert own_contract.owner_id == int(a_user)
    assert own_contract.organization == "Renamed"


def test_duplicate_on_own_unit_works(a_and_b):
    a, a_user, _, _ = a_and_b
    unit = TripUnit.objects.filter(owner_id=a_user).first()
    assert a.post(f"/t/units/{unit.pk}/duplicate/").status_code == 201


def test_contract_numbers_independent_per_owner(a_and_b):
    _, a_user, _, b_user = a_and_b
    assert Contract.objects.get(owner_id=a_user, number=24817)
    assert Contract.objects.get(owner_id=b_user, number=24817)


def test_anonymous_cannot_read_owned_rows(client, a_and_b):
    assert client.get("/t/contracts/").status_code == 403
    assert client.get("/t/units/").status_code == 403


def test_service_creates_separate_sandboxes(reference):
    tz = resolve_timezone(None)
    one = create_demo_session(ip="1.1.1.1", tz=tz)
    two = create_demo_session(ip="1.1.1.1", tz=tz)
    assert one.user != two.user
    assert one.ip_hash == two.ip_hash != "1.1.1.1"
    assert Contract.objects.filter(owner=one.user).count() == 12


# ---------------------------------------------------------------------------
# Real endpoints. Add each new owned endpoint here as it is built.
# ---------------------------------------------------------------------------


def test_contract_list_only_shows_own_contracts(a_and_b):
    a, a_user, _, _ = a_and_b
    ids = {row["id"] for row in a.get("/api/contracts/").json()["results"]}
    assert ids == set(Contract.objects.filter(owner_id=a_user).values_list("id", flat=True))


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_contract_detail_of_other_owner_returns_404(a_and_b, b_rows, method):
    a, _, _, _ = a_and_b
    contract, _ = b_rows
    response = getattr(a, method)(
        f"/api/contracts/{contract.pk}/",
        data={"organization": "x"},
        content_type="application/json",
    )
    assert response.status_code == 404
    contract.refresh_from_db()
    assert contract.organization != "x"


def test_contract_lookup_never_finds_other_owners_contract(a_and_b, b_rows):
    a, a_user, b, _ = a_and_b
    contract, _ = b_rows
    Contract.objects.filter(pk=contract.pk).update(number=55555)
    assert b.get("/api/contracts/lookup/", {"number": "55555"}).status_code == 200
    assert a.get("/api/contracts/lookup/", {"number": "55555"}).status_code == 404
    own = a.get("/api/contracts/lookup/", {"number": "24817"}).json()["id"]
    assert Contract.objects.get(pk=own).owner_id == int(a_user)


def test_next_number_and_create_are_per_owner(a_and_b):
    a, a_user, b, b_user = a_and_b
    Contract.objects.filter(owner_id=b_user, number=24844).update(number=30000)
    assert b.get("/api/contracts/next-number/").json() == {"number": 30001}
    assert a.get("/api/contracts/next-number/").json() == {"number": 24845}


def test_contract_search_and_summary_only_cover_own_rows(a_and_b):
    a, _, _, b_user = a_and_b
    Contract.objects.filter(owner_id=b_user, number=24817).update(organization="Only In B")
    data = a.get("/api/contracts/", {"q": "only in b"}).json()
    assert data["results"] == []
    assert data["summary"]["count"] == 0
