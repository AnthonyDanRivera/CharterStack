"""Booking API: rules R02-R10, R14, R28 (booking search), R31-R33."""

import datetime as dt
from decimal import Decimal

import pytest

from charters.models import Contract, TripUnit
from charters.services import MAX_CONTRACTS_PER_OWNER
from charters.timeutil import parse_loose_time, today_in

pytestmark = pytest.mark.django_db

URL = "/api/contracts/"


@pytest.fixture
def api(demo_client):
    return demo_client()


@pytest.fixture
def today():
    from charters.timeutil import resolve_timezone

    return today_in(resolve_timezone(None))


def payload(**overrides):
    body = {
        "status": "booked",
        "organization": "Weehawken Rotary",
        "group_name": "Spring Gala",
        "passengers": 40,
        "contact_name": "Pat Lee",
        "contact_phone": "(201) 555-0100",
        "begin_date": "2026-12-01",
        "spot_time": "0645",
        "start_time": "7:15",
        "return_date": "2026-12-01",
        "return_time": "6p",
        "pickup": {"location": "Town Hall", "address": "400 Park Ave", "zip": "07086"},
        "destination": {"address": "1 Main St", "city": "Hoboken", "state": "NJ"},
        "bus_count": 1,
        "terminal": "NJ",
        "size_requirement": "56-pax coach",
        "total_price": "$1,200.00",
    }
    body.update(overrides)
    return body


def post(api, **overrides):
    return api.post(URL, payload(**overrides), content_type="application/json")


def patch(api, pk, body):
    return api.patch(f"{URL}{pk}/", body, content_type="application/json")


def contract_id(api, number):
    return api.get(f"{URL}lookup/", {"number": str(number)}).json()["id"]


# --- R02 smart time input ---------------------------------------------------


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("7", "07:00"),
        ("07", "07:00"),
        ("730", "07:30"),
        ("0730", "07:30"),
        ("7:30", "07:30"),
        ("1915", "19:15"),
        ("19:15", "19:15"),
        ("7p", "19:00"),
        ("7 pm", "19:00"),
        ("7:30PM", "19:30"),
        ("7:30 a.m.", "07:30"),
        ("12a", "00:00"),
        ("12p", "12:00"),
        ("0", "00:00"),
        ("23:59", "23:59"),
    ],
)
def test_r02_time_normalization(typed, expected):
    assert parse_loose_time(typed).strftime("%H:%M") == expected


@pytest.mark.parametrize("typed", ["25", "7:75", "abc", "2400", "13p", "0p", "7:30:00", ""])
def test_r02_invalid_times_rejected(typed):
    with pytest.raises(ValueError, match="Enter a valid time"):
        parse_loose_time(typed)


@pytest.mark.parametrize("typed", ["ow", "OW", "one way", "One Way"])
def test_r02_one_way_only_for_return_time(typed):
    assert parse_loose_time(typed, allow_one_way=True) is None
    with pytest.raises(ValueError):
        parse_loose_time(typed)


def test_r02_api_normalizes_typed_times(api):
    body = post(api, spot_time="645", start_time="7:15", return_time="6:30pm").json()
    assert (body["spot_time"], body["start_time"], body["return_time"]) == (
        "06:45",
        "07:15",
        "18:30",
    )


def test_r02_api_rejects_bad_time_with_form_message(api):
    response = post(api, start_time="7:75")
    assert response.status_code == 400
    assert response.json()["start_time"] == [
        "Start time isn’t a valid time. Try something like 07:15."
    ]


def test_r02_one_way_not_allowed_for_spot_time(api):
    response = post(api, spot_time="ow")
    assert response.json()["spot_time"] == [
        "Spot time isn’t a valid time. Try something like 06:45."
    ]


# --- R03 one way --------------------------------------------------------------


@pytest.mark.parametrize("value", [None, "ow", "one way"])
def test_r03_one_way_is_null_return_time(api, value):
    response = post(api, return_time=value)
    assert response.status_code == 201, response.json()
    assert response.json()["return_time"] is None
    assert response.json()["return_date"] == "2026-12-01"


def test_r03_one_way_still_needs_return_date(api):
    body = payload(return_time="ow")
    del body["return_date"]
    response = api.post(URL, body, content_type="application/json")
    assert response.json()["return_date"] == ["Pick a return date."]


def test_r03_missing_return_time_is_required_not_one_way(api):
    body = payload()
    del body["return_time"]
    response = api.post(URL, body, content_type="application/json")
    assert response.json()["return_time"] == ["Enter a return time, or pick One way."]


# --- R04 / R05 date and time order ------------------------------------------


def test_r04_return_before_begin_rejected(api):
    response = post(api, begin_date="2026-12-02", return_date="2026-12-01")
    assert response.status_code == 400
    assert response.json()["return_date"] == ["Return date can’t be before the begin date."]


def test_r04_return_same_day_allowed(api):
    assert post(api, begin_date="2026-12-01", return_date="2026-12-01").status_code == 201


def test_r04_checked_on_partial_update(api):
    pk = post(api).json()["id"]
    response = patch(api, pk, {"return_date": "2026-11-30"})
    assert response.json()["return_date"] == ["Return date can’t be before the begin date."]


def test_r05_spot_after_start_rejected(api):
    response = post(api, spot_time="07:30", start_time="07:15")
    assert response.status_code == 400
    assert response.json()["spot_time"] == ["Spot time can’t be after the start time."]


def test_r05_spot_equal_to_start_allowed(api):
    assert post(api, spot_time="07:15", start_time="07:15").status_code == 201


def test_r05_checked_on_partial_update(api):
    pk = post(api).json()["id"]
    assert patch(api, pk, {"spot_time": "08:00"}).json()["spot_time"] == [
        "Spot time can’t be after the start time."
    ]


# --- R06 server-assigned numbers --------------------------------------------


def test_r06_next_number_is_highest_plus_one(api):
    assert api.get(f"{URL}next-number/").json() == {"number": 24845}


def test_r06_create_assigns_number_and_ignores_typed_one(api):
    response = post(api, number=11111)
    assert response.status_code == 201
    assert response.json()["number"] == 24845
    assert post(api).json()["number"] == 24846
    assert api.get(f"{URL}next-number/").json() == {"number": 24847}


def test_r06_number_cannot_be_changed(api):
    pk = contract_id(api, 24817)
    patch(api, pk, {"number": 1})
    assert api.get(f"{URL}{pk}/").json()["number"] == 24817


def test_r06_empty_sandbox_starts_at_24811(api):
    Contract.objects.all().delete()
    assert api.get(f"{URL}next-number/").json() == {"number": 24811}


# --- R07 contract status ----------------------------------------------------


def test_r07_status_defaults_to_booked(api):
    body = payload()
    del body["status"]
    assert api.post(URL, body, content_type="application/json").json()["status"] == "booked"


def test_r07_quote_and_cancelled_visible_in_booking(api, today):
    statuses = {r["number"]: r["status"] for r in api.get(URL).json()["results"]}
    assert statuses[24841] == "quote"
    assert statuses[24844] == "cancelled"


def test_r07_cancelling_keeps_contract_and_units(api):
    pk = contract_id(api, 24817)
    assert patch(api, pk, {"status": "cancelled"}).status_code == 200
    contract = Contract.objects.get(pk=pk)
    assert contract.status == "cancelled"
    assert contract.units.count() == 1


def test_r07_invalid_status_rejected(api):
    assert "status" in post(api, status="pending").json()


# --- R08 required fields ----------------------------------------------------

REQUIRED = [
    ("organization", "organization", "Enter the organization."),
    ("group_name", "group_name", "Enter the group name."),
    ("passengers", "passengers", "Enter the number of passengers."),
    ("contact_name", "contact_name", "Enter the group contact name."),
    ("contact_phone", "contact_phone", "Enter the group contact phone."),
    ("begin_date", "begin_date", "Pick a begin date."),
    ("spot_time", "spot_time", "Enter a spot time."),
    ("start_time", "start_time", "Enter a start time."),
    ("return_date", "return_date", "Pick a return date."),
    ("return_time", "return_time", "Enter a return time, or pick One way."),
    ("bus_count", "bus_count", "Enter how many buses (at least 1)."),
    ("terminal", "terminal", "Pick a terminal."),
    ("size_requirement", "size_requirement", "Pick a size requirement."),
    ("total_price", "total_price", "Enter the total price."),
]


@pytest.mark.parametrize(("field", "key", "message"), REQUIRED)
def test_r08_required_field_missing(api, field, key, message):
    body = payload()
    del body[field]
    response = api.post(URL, body, content_type="application/json")
    assert response.status_code == 400
    assert response.json()[key] == [message]


@pytest.mark.parametrize(("field", "key", "message"), REQUIRED)
def test_r08_required_field_blank(api, field, key, message):
    response = post(api, **{field: ""})
    assert response.status_code == 400
    assert response.json()[key] == [message]


@pytest.mark.parametrize(("side", "label"), [("pickup", "pickup"), ("destination", "destination")])
def test_r08_location_address_state_city_required(api, side, label):
    response = post(api, **{side: {"address": " ", "state": "", "city": ""}})
    assert response.status_code == 400
    assert response.json()[side] == {
        "city": [f"Pick the {label} state and city."],
        "address": [f"Enter the {label} address."],
    }


def test_r08_unknown_state_rejected(api):
    response = post(api, destination={"address": "1 Main", "city": "Paris", "state": "ZZ"})
    assert response.json()["destination"] == {"city": ["Pick the destination state and city."]}


def test_r08_optional_fields_can_be_left_out(api):
    body = payload()
    body["pickup"] = {"address": "400 Park Ave", "city": "Weehawken", "state": "NJ"}
    response = api.post(URL, body, content_type="application/json")
    assert response.status_code == 201, response.json()
    data = response.json()
    assert (data["itinerary"], data["info"], data["requested_driver"]) == ("", "", None)
    assert (data["deposit_required"], data["total_paid"]) == ("0.00", "0.00")
    assert data["pickup"]["location"] == "" and data["pickup"]["zip"] == ""


@pytest.mark.parametrize("passengers", [0, -1, "many"])
def test_r08_passengers_at_least_one(api, passengers):
    assert post(api, passengers=passengers).json()["passengers"] == [
        "Enter the number of passengers."
    ]


@pytest.mark.parametrize("count", [0, -1, "two"])
def test_r08_bus_count_at_least_one(api, count):
    assert post(api, bus_count=count).json()["bus_count"] == ["Enter how many buses (at least 1)."]


def test_r08_bus_count_has_no_upper_limit(api):
    data = post(api, bus_count=45).json()
    assert data["bus_count"] == 45
    assert len(data["units"]) == 45
    assert data["units"][-1]["display_number"] == "24845-45"


def test_r08_long_text_capped(api):
    response = post(api, info="x" * 2001)
    assert response.status_code == 400
    assert "info" in response.json()


def test_r08_partial_update_does_not_require_everything(api):
    pk = contract_id(api, 24817)
    response = patch(api, pk, {"passengers": 50})
    assert response.status_code == 200
    assert response.json()["passengers"] == 50


def test_r08_partial_update_cannot_blank_required_field(api):
    pk = contract_id(api, 24817)
    assert patch(api, pk, {"organization": ""}).json()["organization"] == [
        "Enter the organization."
    ]
    assert patch(api, pk, {"pickup": {"address": ""}}).json()["pickup"] == {
        "address": ["Enter the pickup address."]
    }


# --- R09 ZIP auto-fill ------------------------------------------------------


def test_r09_zip_endpoint(api):
    assert api.get("/api/zip/07087/").json() == {
        "zip": "07087",
        "city": "Union City",
        "state": "NJ",
        "county": "Hudson County",
    }
    assert api.get("/api/zip/99999/").status_code == 404


def test_r09_known_zip_fills_city_state_and_county(api):
    data = post(api).json()  # pickup has only an address and ZIP 07086
    assert data["pickup"] == {
        "location": "Town Hall",
        "address": "400 Park Ave",
        "city": "Weehawken",
        "state": "NJ",
        "zip": "07086",
        "county": "Hudson County",
    }


def test_r09_county_is_read_only(api):
    body = payload()
    body["destination"]["county"] = "Made Up County"
    data = api.post(URL, body, content_type="application/json").json()
    assert data["destination"]["county"] == ""  # no ZIP given


def test_r09_changing_zip_updates_county(api):
    pk = contract_id(api, 24817)
    data = patch(api, pk, {"destination": {"zip": "07030"}}).json()
    assert data["destination"]["county"] == "Hudson County"
    # Only the ZIP was sent, so the known ZIP fills city and state too (R09).
    assert (data["destination"]["city"], data["destination"]["state"]) == ("Hoboken", "NJ")
    data = patch(api, pk, {"destination": {"zip": ""}}).json()
    assert data["destination"]["county"] == ""


def test_r09_typed_city_kept_when_sent_with_zip(api):
    body = payload()
    body["pickup"] = {"address": "1 Pier", "city": "Hoboken", "state": "NJ", "zip": "07087"}
    data = api.post(URL, body, content_type="application/json").json()
    assert data["pickup"]["city"] == "Hoboken"
    assert data["pickup"]["county"] == "Hudson County"


def test_r09_unknown_zip_leaves_county_blank(api):
    body = payload()
    body["destination"]["zip"] = "99999"
    data = api.post(URL, body, content_type="application/json").json()
    assert data["destination"]["county"] == ""


def test_r09_bad_zip_format_rejected(api):
    body = payload()
    body["destination"]["zip"] = "7030"
    assert api.post(URL, body, content_type="application/json").json()["destination"] == {
        "zip": ["Enter a 5-digit ZIP code."]
    }


# --- R10 delete -------------------------------------------------------------


def test_r10_delete_removes_contract_and_units(api):
    pk = contract_id(api, 24823)
    assert api.delete(f"{URL}{pk}/").status_code == 204
    assert not Contract.objects.filter(pk=pk).exists()
    assert not TripUnit.objects.filter(contract_id=pk).exists()
    assert api.get(f"{URL}{pk}/").status_code == 404


# --- R13 money through the API ----------------------------------------------


@pytest.mark.parametrize("typed", ["1200", "1,200", "$1,200.00"])
def test_r13_api_accepts_loose_money(api, typed):
    assert post(api, total_price=typed).json()["total_price"] == "1200.00"


def test_r13_api_money_messages(api):
    data = post(api, total_price="abc", deposit_required="-5", total_paid="lots").json()
    assert data["total_price"] == ["Enter the total price."]
    assert data["deposit_required"] == ["Deposit must be a dollar amount."]
    assert data["total_paid"] == ["Total paid must be a dollar amount."]


def test_r13_api_deposit_above_price(api):
    data = post(api, total_price="500", deposit_required="600").json()
    assert data["deposit_required"] == ["Deposit can’t be more than the total price."]


def test_r13_api_deposit_checked_against_saved_price(api):
    pk = post(api, total_price="500").json()["id"]
    assert "deposit_required" in patch(api, pk, {"deposit_required": "501"}).json()


def test_pricing_endpoint_matches_r11_r12(api):
    data = api.get(
        f"{URL}pricing/", {"total_price": "$2,900", "deposit_required": "600", "total_paid": "600"}
    ).json()
    assert data == {
        "balance_due": "2300.00",
        "payment_status": "Deposit paid",
        "payment_tone": "part",
    }
    cancelled = api.get(
        f"{URL}pricing/", {"total_price": "1100", "total_paid": "400", "status": "cancelled"}
    ).json()
    assert cancelled["payment_status"] == "Cancelled · $400.00 kept"
    assert cancelled["balance_due"] == "0.00"
    blank = api.get(f"{URL}pricing/", {"total_price": ""}).json()
    assert blank == {"balance_due": None, "payment_status": "—", "payment_tone": "none"}


# --- R14 units follow bus count ---------------------------------------------


def unit_numbers(pk):
    return [
        (u.is_duplicate, u.unit_number)
        for u in TripUnit.objects.filter(contract_id=pk).order_by("is_duplicate", "unit_number")
    ]


def test_r14_create_makes_bus_count_units(api):
    data = post(api, bus_count=3).json()
    assert [u["display_number"] for u in data["units"]] == ["24845-1", "24845-2", "24845-3"]


def test_r14_raising_bus_count_adds_units_at_end(api):
    pk = contract_id(api, 24823)
    u1 = TripUnit.objects.get(contract_id=pk, unit_number=1)
    patch(api, pk, {"bus_count": 4})
    assert unit_numbers(pk) == [(False, 1), (False, 2), (False, 3), (False, 4)]
    u1.refresh_from_db()
    assert u1.driver.name == "Luis Ortega"  # existing units untouched


def test_r14_lowering_bus_count_removes_highest_regular_units(api):
    pk = post(api, bus_count=3).json()["id"]
    TripUnit.objects.create(contract_id=pk, unit_number=1, is_duplicate=True)
    data = patch(api, pk, {"bus_count": 1}).json()
    assert unit_numbers(pk) == [(False, 1), (True, 1)]
    assert [u["display_number"] for u in data["units"]] == ["24845", "24845-D1"]


def test_r14_duplicates_never_touched(api):
    pk = contract_id(api, 24817)
    TripUnit.objects.create(contract_id=pk, unit_number=1, is_duplicate=True)
    TripUnit.objects.create(contract_id=pk, unit_number=2, is_duplicate=True)
    patch(api, pk, {"bus_count": 2})
    patch(api, pk, {"bus_count": 1})
    assert unit_numbers(pk) == [(False, 1), (True, 1), (True, 2)]


def test_r14_unchanged_bus_count_keeps_units(api):
    pk = contract_id(api, 24823)
    before = list(TripUnit.objects.filter(contract_id=pk).values_list("pk", flat=True))
    patch(api, pk, {"bus_count": 2, "organization": "Renamed"})
    assert list(TripUnit.objects.filter(contract_id=pk).values_list("pk", flat=True)) == before


# --- Detail shape -----------------------------------------------------------


def test_contract_detail_shape(api):
    data = api.get(f"{URL}{contract_id(api, 24811)}/").json()
    assert data["number"] == 24811
    assert data["pickup"]["county"] == "Hudson County"
    assert data["terminal"] == "NJ"
    assert data["requested_driver_name"] == "Marcus Bell"
    assert isinstance(data["requested_driver"], int)
    assert (data["total_price"], data["balance_due"]) == ("2450.00", "0.00")
    assert (data["payment_status"], data["payment_tone"]) == ("Paid in full", "ok")
    assert data["spot_time"] == "05:00"
    unit = data["units"][0]
    assert unit["display_number"] == "24811"
    assert (unit["driver"], unit["driver_phone"], unit["bus"]) == (
        "Marcus Bell",
        "(201) 555-0181",
        "4512",
    )
    assert unit["report_time"] == "04:15"
    assert unit["confirmed_at"].endswith(("-05:00", "-04:00"))


def test_confirmed_at_rendered_in_visitor_time_zone(demo_client):
    api = demo_client(**{"X-Timezone": "Asia/Tokyo"})
    data = api.get(f"{URL}{contract_id(api, 24811)}/").json()
    assert data["units"][0]["confirmed_at"].endswith("+09:00")


def test_put_not_allowed(api):
    pk = contract_id(api, 24817)
    assert api.put(f"{URL}{pk}/", payload(), content_type="application/json").status_code == 405


def test_demo_limit_reached(api, monkeypatch):
    monkeypatch.setattr("charters.services.MAX_CONTRACTS_PER_OWNER", Contract.objects.count())
    response = post(api)
    assert response.status_code == 400
    assert response.json() == {"non_field_errors": ["Demo limit reached."]}
    assert MAX_CONTRACTS_PER_OWNER == 200


# --- R32 list filter, R24 range, R28 booking search, R33 summary -----------


def numbers(response):
    return [r["number"] for r in response.json()["results"]]


def test_r32_list_filters(api):
    assert len(numbers(api.get(URL))) == 12
    assert len(numbers(api.get(URL, {"status": "all"}))) == 12
    assert 24844 not in numbers(api.get(URL, {"status": "active"}))
    assert len(numbers(api.get(URL, {"status": "active"}))) == 11
    assert len(numbers(api.get(URL, {"status": "booked"}))) == 10
    assert numbers(api.get(URL, {"status": "quote"})) == [24841]
    assert numbers(api.get(URL, {"status": "cancelled"})) == [24844]


def test_r32_bad_status_filter_rejected(api):
    assert api.get(URL, {"status": "nope"}).status_code == 400


def test_r32_filter_combines_with_range_and_search(api, today):
    tomorrow = (today + dt.timedelta(days=1)).isoformat()
    rows = numbers(
        api.get(URL, {"start": tomorrow, "end": tomorrow, "status": "active", "q": "nj"})
    )
    assert 24844 not in rows  # cancelled, excluded by "active"
    assert rows == numbers(
        api.get(URL, {"start": tomorrow, "end": tomorrow, "status": "active", "q": "NJ"})
    )


def test_r24_booking_range_overlap(api, today):
    t = today.isoformat()
    rows = numbers(api.get(URL, {"start": t, "end": t}))
    # Five contracts begin on the base day.
    assert rows == [24811, 24814, 24817, 24820, 24823]
    day3 = (today + dt.timedelta(days=3)).isoformat()
    # 24838 runs base+2 to base+5, so it overlaps base+3 without beginning on it.
    assert numbers(api.get(URL, {"start": day3, "end": day3})) == [24838]


def test_r24_list_ordered_by_begin_date_then_number(api):
    rows = api.get(URL).json()["results"]
    keys = [(r["begin_date"], r["number"]) for r in rows]
    assert keys == sorted(keys)


def test_r24_single_bound_means_one_day(api, today):
    t = today.isoformat()
    assert numbers(api.get(URL, {"start": t})) == numbers(api.get(URL, {"start": t, "end": t}))


def test_r24_end_before_start_rejected(api):
    assert api.get(URL, {"start": "2026-11-10", "end": "2026-11-09"}).status_code == 400


@pytest.mark.parametrize(
    ("q", "expected"),
    [
        ("24817", [24817]),
        ("hoboken youth", [24811]),  # organization, case-insensitive
        ("u14", [24811]),  # group name
        ("dana price", [24811]),  # contact name
        ("555-0142", [24811]),  # phone
        ("allentown", [24811]),  # destination city
        ("stevens park", [24811]),  # pickup location name
        ("lehigh valley sports", [24811]),  # destination location name
        ("zzzz", []),
    ],
)
def test_r28_booking_search(api, q, expected):
    assert numbers(api.get(URL, {"q": q})) == expected


def test_r33_summary(api):
    summary = api.get(URL).json()["summary"]
    expected_balance = sum((c.balance_due for c in Contract.objects.all()), Decimal("0"))
    assert summary == {
        "count": 12,
        "booked": 10,
        "quotes": 1,
        "cancelled": 1,
        "balance_due": f"{expected_balance:.2f}",
    }


def test_r33_cancelled_contributes_zero_balance(api):
    data = api.get(URL, {"status": "cancelled"}).json()
    assert data["results"][0]["balance_due"] == "0.00"
    assert data["summary"]["balance_due"] == "0.00"


def test_r33_summary_follows_search(api):
    summary = api.get(URL, {"q": "24817"}).json()["summary"]
    assert summary == {
        "count": 1,
        "booked": 1,
        "quotes": 0,
        "cancelled": 0,
        "balance_due": "950.00",
    }


def test_list_row_shape(api):
    row = next(r for r in api.get(URL).json()["results"] if r["number"] == 24817)
    assert row == {
        "id": row["id"],
        "number": 24817,
        "status": "booked",
        "begin_date": row["begin_date"],
        "start_time": "07:15",
        "organization": "Union City Public Schools",
        "group_name": "9th Grade Biology",
        "pickup_city": "Union City",
        "dest_city": "Jersey City",
        "bus_count": 1,
        "total_price": "950.00",
        "balance_due": "950.00",
        "payment_status": "Unpaid",
        "payment_tone": "warn",
    }


# --- R31 lookup -------------------------------------------------------------


@pytest.mark.parametrize("typed", ["24823", "24823-1", "24823-2", " 24823 ", "24823-d1"])
def test_r31_lookup_resolves_unit_numbers_to_contract(api, typed):
    pk = Contract.objects.get(number=24823).pk
    assert api.get(f"{URL}lookup/", {"number": typed}).json() == {"id": pk}


def test_r31_lookup_duplicate_number(api):
    pk = Contract.objects.get(number=24817).pk
    assert api.get(f"{URL}lookup/", {"number": "24817-D1"}).json() == {"id": pk}


@pytest.mark.parametrize("typed", ["99999", "abc", "", "2481"])
def test_r31_lookup_not_found(api, typed):
    response = api.get(f"{URL}lookup/", {"number": typed})
    assert response.status_code == 404
    assert response.json() == {"detail": f"No contract {typed} found."}


def test_r31_lookup_finds_quotes_and_cancelled(api):
    assert api.get(f"{URL}lookup/", {"number": "24841"}).status_code == 200
    assert api.get(f"{URL}lookup/", {"number": "24844"}).status_code == 200


# --- Reference --------------------------------------------------------------


def test_reference_endpoint(api):
    data = api.get("/api/reference/").json()
    assert [t["code"] for t in data["terminals"]] == ["CT", "MA", "NJ", "NY", "PA"]
    assert len(data["drivers"]) == 10 and set(data["drivers"][0]) == {"id", "name", "phone"}
    assert len(data["buses"]) == 8
    assert data["size_options"][0] == "56-pax coach" and len(data["size_options"]) == 8
    assert {"code": "DC", "name": "District of Columbia"} in data["states"]
    assert "Secaucus" in data["cities"]["NJ"]
    assert data["cities"]["NJ"] == sorted(data["cities"]["NJ"])


def test_reference_hides_inactive_drivers(api):
    from charters.models import Driver

    Driver.objects.filter(name="Sam Whitaker").update(is_active=False)
    names = [d["name"] for d in api.get("/api/reference/").json()["drivers"]]
    assert "Sam Whitaker" not in names


def test_booking_endpoints_require_login(client):
    for url in [URL, f"{URL}next-number/", "/api/reference/", "/api/zip/07030/"]:
        assert client.get(url).status_code == 403
