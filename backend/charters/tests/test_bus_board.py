"""Bus board API: rules R34 (fleet layout) and R35 (assignments).

Test fleet (seed_test.json): NJ has 4512, 4520, 4561 (MCI J4500, 56), 4533
(Prevost H3-45, 57, lift), 4547 (Van Hool CX45, 56) and 2207 (Shuttle, 28);
NY has 3108 and PA 3115 (Minicoach, 35). On the base day (T) 4512 runs 24811
and 4533 runs 24814; 3108 runs 24820 from T to T+2.
"""

import datetime as dt

import pytest

from charters.models import Bus, Contract, Terminal, TripUnit
from charters.timeutil import resolve_timezone, today_in

pytestmark = pytest.mark.django_db
URL = "/api/buses/board/"


@pytest.fixture
def api(demo_client):
    return demo_client()


@pytest.fixture
def T():
    return today_in(resolve_timezone(None))


def get(api, T, **params):
    params.setdefault("start", T.isoformat())
    params.setdefault("end", params["start"])
    return api.get(URL, params).json()


def layout(data):
    return [(r["model"], [b["number"] for b in r["buses"]]) for r in data["rows"]]


def bus(data, number):
    return next(b for r in data["rows"] for b in r["buses"] if b["number"] == number)


# --- R34 fleet layout -------------------------------------------------------


def test_r34_one_row_per_model_largest_first(api, T):
    assert layout(get(api, T)) == [
        ("Prevost H3-45", ["4533"]),
        ("MCI J4500", ["4512", "4520", "4561"]),
        ("Van Hool CX45", ["4547"]),
        ("Shuttle", ["2207"]),
    ]


def test_r34_only_the_selected_terminal(api, T):
    assert layout(get(api, T, terminal="NY")) == [("Minicoach", ["3108"])]
    assert get(api, T, terminal="pa")["terminal"] == {"code": "PA", "name": "Pennsylvania"}


def test_r34_defaults_to_nj(api, T):
    assert api.get(URL).json()["terminal"]["code"] == "NJ"


def test_r34_bus_numbers_increase_numerically(api, T):
    nj = Terminal.objects.get(code="NJ")
    Bus.objects.create(number="999", seats=56, model="MCI J4500", terminal=nj)
    Bus.objects.create(number="10000", seats=56, model="MCI J4500", terminal=nj)
    row = dict(layout(get(api, T)))["MCI J4500"]
    assert row == ["999", "4512", "4520", "4561", "10000"]


def test_r34_inactive_and_homeless_buses_hidden(api, T):
    Bus.objects.filter(number="4520").update(is_active=False)
    Bus.objects.create(number="4599", seats=56, model="MCI J4500", terminal=None)
    row = dict(layout(get(api, T)))["MCI J4500"]
    assert row == ["4512", "4561"]


def test_r34_unknown_terminal_rejected(api, T):
    response = api.get(URL, {"terminal": "ZZ"})
    assert response.status_code == 400
    assert response.json() == {"terminal": ["Unknown terminal."]}


def test_r34_bus_fields(api, T):
    b = bus(get(api, T), "4533")
    assert (b["seats"], b["has_wc_lift"]) == (57, True)


# --- R35 assignments --------------------------------------------------------


def test_r35_assigned_and_available_buses(api, T):
    data = get(api, T)
    a = bus(data, "4512")
    assert a["available"] is False
    assert a["assignments"] == [
        {
            "unit_id": a["assignments"][0]["unit_id"],
            "display_number": "24811",
            "driver": "Marcus Bell",
            "begin_date": T.isoformat(),
            "return_date": T.isoformat(),
            "start_time": "05:30",
            "organization": "Hoboken Youth Soccer League",
        }
    ]
    assert bus(data, "4520") == {**bus(data, "4520"), "available": True, "assignments": []}
    assert data["counts"] == {"buses": 6, "available": 4}


def test_r35_multi_day_trip_overlaps_later_days(api, T):
    later = (T + dt.timedelta(days=2)).isoformat()
    data = get(api, T, terminal="NY", start=later)
    assert [a["display_number"] for a in bus(data, "3108")["assignments"]] == ["24820"]


def test_r35_range_lists_every_trip_in_order(api, T):
    unit = TripUnit.objects.get(contract__number=24817)
    unit.bus = Bus.objects.get(number="4512")
    unit.save()
    tomorrow = (T + dt.timedelta(days=1)).isoformat()
    data = get(api, T, start=T.isoformat(), end=tomorrow)
    # 24811 starts 05:30, 24817 at 07:15, both today.
    assert [a["display_number"] for a in bus(data, "4512")["assignments"]] == ["24811", "24817"]


def test_r35_cancelled_unit_frees_the_bus(api, T):
    TripUnit.objects.filter(contract__number=24811).update(status="cancelled")
    assert bus(get(api, T), "4512")["available"] is True


def test_r35_cancelled_contract_frees_the_bus(api, T):
    Contract.objects.filter(number=24811).update(status="cancelled")
    assert bus(get(api, T), "4512")["available"] is True


def test_r35_quotes_never_listed(api, T):
    unit = TripUnit.objects.get(contract__number=24841)  # a quote, 12 days out
    unit.bus = Bus.objects.get(number="4520")
    unit.save()
    quote_day = Contract.objects.get(number=24841).begin_date.isoformat()
    assert bus(get(api, T, start=quote_day), "4520")["available"] is True


def test_bus_board_requires_login(client):
    assert client.get(URL).status_code == 403
