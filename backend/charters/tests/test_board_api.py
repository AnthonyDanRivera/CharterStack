"""Dispatch board API: rules R07, R16-R30 and the Excel export.

The seeded sandbox puts the base day on today (T). On T the board shows
24811, 24814, 24817 (single-day) and 24820, 24823-1, 24823-2 (multi-day
trips that begin on T): 6 trips, 3 need driver or bus, 4 pending confirmation.
"""

import datetime as dt
from io import BytesIO
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from charters.board import day_label, normalize_initials
from charters.models import Bus, Contract, Driver, TripUnit
from charters.timeutil import resolve_timezone, today_in

pytestmark = pytest.mark.django_db

NY = ZoneInfo("America/New_York")


@pytest.fixture
def api(demo_client):
    return demo_client()


@pytest.fixture
def T():
    return today_in(resolve_timezone(None))


def day(T, n=0):
    return (T + dt.timedelta(days=n)).isoformat()


def board(api, T, **params):
    params.setdefault("start", day(T))
    params.setdefault("end", params["start"])
    return api.get("/api/board/", params).json()


def numbers(data):
    return [r["display_number"] for r in data["rows"]]


def unit_id(display):
    number, _, rest = display.partition("-")
    qs = TripUnit.objects.filter(contract__number=int(number))
    if rest.startswith("D"):
        return qs.get(is_duplicate=True, unit_number=int(rest[1:])).pk
    return qs.get(is_duplicate=False, unit_number=int(rest or 1)).pk


def post(api, display, action, **body):
    return api.post(
        f"/api/units/{unit_id(display)}/{action}/", body, content_type="application/json"
    )


def patch(api, display, body):
    return api.patch(f"/api/units/{unit_id(display)}/", body, content_type="application/json")


def at(hour, minute):
    """Freeze the clock at a New York wall time today."""
    T = today_in(NY)
    return mock.patch(
        "django.utils.timezone.now",
        return_value=dt.datetime(T.year, T.month, T.day, hour, minute, 17, tzinfo=NY),
    )


# --- Basic board ------------------------------------------------------------


def test_board_defaults_to_today(api, T):
    data = api.get("/api/board/").json()
    assert numbers(data) == ["24811", "24814", "24817", "24820", "24823-1", "24823-2"]
    assert data["counts"] == {"trips": 6, "need_driver_or_bus": 3, "pending_confirmation": 4}


def test_board_row_shape(api, T):
    row = next(r for r in board(api, T)["rows"] if r["display_number"] == "24811")
    assert row["day_label"] == "1/1"
    assert row["terminal"] == "NJ"
    assert (row["start_time"], row["spot_time"], row["report_time"]) == ("05:30", "05:00", "04:15")
    assert row["pickup"] == "Stevens Park, Hoboken, NJ"
    assert row["destination"] == "Lehigh Valley Sports Complex, Allentown, PA"
    assert (row["driver"], row["driver_phone"]) == ("Marcus Bell", "(201) 555-0181")
    assert (row["bus"], row["bus_seats"]) == ("4512", 56)
    assert row["confirm_initials"] == "AR"
    assert row["status"] == ""
    assert row["actual_report_late"] is False


def test_unit_detail_has_full_addresses(api, T):
    data = api.get(f"/api/units/{unit_id('24811')}/").json()
    assert data["pickup"] == "Stevens Park, Hudson St & 4th St, Hoboken, NJ 07030"
    assert (
        data["destination"] == "Lehigh Valley Sports Complex, 3100 Lehigh St, Allentown, PA 18101"
    )


def test_short_place_line_without_location_name():
    from charters.board import short_place_line

    assert short_place_line("", "Hoboken", "NJ") == "Hoboken, NJ"
    assert short_place_line(" Stevens Park ", "Hoboken", "NJ") == "Stevens Park, Hoboken, NJ"


def test_refreshed_at_in_visitor_time_zone(demo_client, T):
    api = demo_client(**{"X-Timezone": "Asia/Tokyo"})
    assert api.get("/api/board/").json()["refreshed_at"].endswith("+09:00")


def test_board_requires_login(client):
    assert client.get("/api/board/").status_code == 403


# --- R07 quotes and cancelled contracts -------------------------------------


def test_r07_quote_hidden_from_board(api, T):
    data = board(api, T, start=day(T, 12), view="all")
    assert "24841" not in numbers(data)
    assert data["counts"]["trips"] == 0


def test_r07_booked_quote_appears_once_booked(api, T):
    Contract.objects.filter(number=24841).update(status="booked")
    assert numbers(board(api, T, start=day(T, 12))) == ["24841"]


def test_r07_cancelled_contract_units_show_cancelled(api, T):
    row = next(r for r in board(api, T, start=day(T, 1))["rows"] if r["display_number"] == "24844")
    assert row["status"] == "cancelled"


def test_r07_cancelled_contract_wins_over_unit_status(api, T):
    TripUnit.objects.filter(contract__number=24817).update(status="onloc")
    Contract.objects.filter(number=24817).update(status="cancelled")
    row = next(r for r in board(api, T)["rows"] if r["display_number"] == "24817")
    assert row["status"] == "cancelled"


def test_r07_cancelled_excluded_from_counts(api, T):
    Contract.objects.filter(number=24817).update(status="cancelled")
    counts = board(api, T)["counts"]
    assert counts == {"trips": 6, "need_driver_or_bus": 2, "pending_confirmation": 3}


# --- R16 duplicates ---------------------------------------------------------


def test_r16_duplicate_creates_blank_unit(api, T):
    patch(api, "24811", {"dispatch_notes": "Bring cones"})
    response = post(api, "24811", "duplicate")
    assert response.status_code == 201
    dup = response.json()
    assert dup["display_number"] == "24811-D1"
    assert dup["is_duplicate"] is True
    assert (dup["driver"], dup["bus"], dup["report_time"]) == (None, None, None)
    assert (dup["status"], dup["confirm_initials"], dup["dispatch_notes"]) == ("", "", "")
    assert post(api, "24811", "duplicate").json()["display_number"] == "24811-D2"


def test_r16_duplicate_of_multi_bus_creates_exactly_one(api, T):
    post(api, "24823-2", "duplicate")
    assert TripUnit.objects.filter(contract__number=24823, is_duplicate=True).count() == 1


def test_r16_duplicate_sorts_after_regular_units(api, T):
    post(api, "24823-1", "duplicate")
    post(api, "24811", "duplicate")
    assert numbers(board(api, T)) == [
        "24811",
        "24811-D1",
        "24814",
        "24817",
        "24820",
        "24823-1",
        "24823-2",
        "24823-D1",
    ]


def test_r16_delete_duplicate(api, T):
    dup = post(api, "24817", "duplicate").json()
    assert api.delete(f"/api/units/{dup['id']}/").status_code == 204
    assert not TripUnit.objects.filter(pk=dup["id"]).exists()


def test_r16_regular_unit_cannot_be_deleted(api, T):
    response = api.delete(f"/api/units/{unit_id('24817')}/")
    assert response.status_code == 400
    assert response.json() == {"detail": "Only duplicates can be deleted."}
    assert TripUnit.objects.filter(contract__number=24817).count() == 1


def test_r16_duplicate_limit(api, T):
    for _ in range(20):
        assert post(api, "24817", "duplicate").status_code == 201
    response = post(api, "24817", "duplicate")
    assert response.status_code == 400
    assert response.json() == {"detail": "Demo limit reached."}


# --- R17 assignment ---------------------------------------------------------


def test_r17_assign_driver_bus_and_report_time_together(api, T):
    driver = Driver.objects.get(name="Kevin Doyle")
    bus = Bus.objects.get(number="4520")
    data = patch(api, "24817", {"driver": driver.pk, "bus": bus.pk, "report_time": "615"}).json()
    assert (data["driver"], data["bus"], data["report_time"]) == ("Kevin Doyle", "4520", "06:15")
    assert (data["driver_id"], data["bus_id"]) == (driver.pk, bus.pk)
    assert data["warnings"] == []


def test_r17_any_field_may_be_blank(api, T):
    data = patch(api, "24811", {"driver": None, "bus": None, "report_time": ""}).json()
    assert (data["driver"], data["bus"], data["report_time"]) == (None, None, None)


def test_r17_partial_assignment_leaves_other_fields(api, T):
    data = patch(api, "24811", {"report_time": "04:30"}).json()
    assert (data["driver"], data["bus"], data["report_time"]) == ("Marcus Bell", "4512", "04:30")


def test_r17_bad_report_time_rejected(api, T):
    assert patch(api, "24811", {"report_time": "25"}).json() == {
        "report_time": ["Enter a valid time"]
    }


def test_r17_unknown_driver_rejected(api, T):
    assert "driver" in patch(api, "24811", {"driver": 99999}).json()


# --- R18 warnings -----------------------------------------------------------


def bus_id(number):
    return Bus.objects.get(number=number).pk


def test_r18_too_small_single_bus(api, T):
    # 24817 has 48 passengers on one bus.
    data = patch(api, "24817", {"bus": bus_id("3108")}).json()
    assert data["warnings"] == ["Bus #3108 seats 35; this group has 48 passengers."]
    assert data["bus"] == "3108"  # still saved


def test_r18_bus_exactly_big_enough_no_warning(api, T):
    Contract.objects.filter(number=24823).update(passengers=56)  # 28 per bus
    assert patch(api, "24823-2", {"bus": bus_id("2207")}).json()["warnings"] == []


def test_r18_multi_bus_uses_passengers_per_bus(api, T):
    Contract.objects.filter(number=24823).update(passengers=58)  # ceil(58 / 2) = 29
    data = patch(api, "24823-2", {"bus": bus_id("2207")}).json()
    assert data["warnings"] == ["Bus #2207 seats 28; each bus needs about 29 seats."]


def test_r18_no_lift(api, T):
    # 24814 needs WC.
    data = patch(api, "24814", {"bus": bus_id("4512")}).json()
    assert data["warnings"] == ["Bus #4512 has no wheelchair lift; this trip needs WC."]


def test_r18_lift_bus_no_warning(api, T):
    assert patch(api, "24814", {"bus": bus_id("4533")}).json()["warnings"] == []


def test_r18_capacity_warning_comes_first(api, T):
    data = patch(api, "24814", {"bus": bus_id("3108")}).json()
    assert data["warnings"] == [
        "Bus #3108 seats 35; this group has 44 passengers.",
        "Bus #3108 has no wheelchair lift; this trip needs WC.",
    ]


def test_r18_check_before_saving(api, T):
    uid = unit_id("24817")
    data = api.get(f"/api/units/{uid}/check/", {"bus": bus_id("3108")}).json()
    assert data == {"warnings": ["Bus #3108 seats 35; this group has 48 passengers."]}
    assert TripUnit.objects.get(pk=uid).bus is None  # nothing saved
    assert api.get(f"/api/units/{uid}/check/").json() == {"warnings": []}


# --- R19 reported -----------------------------------------------------------


def test_r19_reported_stamps_current_time_to_minute(api, T):
    with at(5, 28):
        data = post(api, "24811", "reported").json()
    assert data["actual_report_time"] == "05:28"
    assert data["actual_report_late"] is True  # report time is 04:15


def test_r19_reported_again_clears(api, T):
    with at(4, 10):
        post(api, "24811", "reported")
        data = post(api, "24811", "reported").json()
    assert data["actual_report_time"] is None


def test_r19_clear_flag_clears(api, T):
    with at(4, 10):
        post(api, "24811", "reported")
        data = post(api, "24811", "reported", clear=True).json()
    assert data["actual_report_time"] is None
    assert post(api, "24811", "reported", clear=True).json()["actual_report_time"] is None


def test_r19_on_time_is_not_late(api, T):
    with at(4, 15):
        assert post(api, "24811", "reported").json()["actual_report_late"] is False


def test_r19_stamp_uses_visitor_time_zone(demo_client, T):
    api = demo_client(**{"X-Timezone": "America/Los_Angeles"})
    with at(8, 0):  # 08:00 New York = 05:00 Los Angeles
        assert post(api, "24811", "reported").json()["actual_report_time"] == "05:00"


# --- R20 / R21 on location and cancelled ------------------------------------


def test_r20_on_location_sets_status_and_time(api, T):
    with at(6, 2):
        data = post(api, "24811", "on-location").json()
    assert (data["status"], data["on_location_time"]) == ("onloc", "06:02")


def test_r20_on_location_again_clears_both(api, T):
    post(api, "24811", "on-location")
    data = post(api, "24811", "on-location").json()
    assert (data["status"], data["on_location_time"]) == ("", None)


def test_r21_cancel_toggles_selected_unit_only(api, T):
    data = post(api, "24823-1", "cancel").json()
    assert data["status"] == "cancelled"
    assert TripUnit.objects.get(pk=unit_id("24823-2")).status == ""
    assert post(api, "24823-1", "cancel").json()["status"] == ""


def test_r21_cancel_clears_on_location_time(api, T):
    post(api, "24811", "on-location")
    data = post(api, "24811", "cancel").json()
    assert (data["status"], data["on_location_time"]) == ("cancelled", None)


def test_r21_on_location_replaces_cancelled(api, T):
    post(api, "24811", "cancel")
    assert post(api, "24811", "on-location").json()["status"] == "onloc"


# --- R22 initials -----------------------------------------------------------


@pytest.mark.parametrize(
    ("typed", "stored"), [("ab", "AB"), ("a.r-1", "AR"), ("abcdef", "ABCD"), ("12", ""), ("", "")]
)
def test_r22_initials_normalized(typed, stored):
    assert normalize_initials(typed) == stored


def test_r22_first_entry_sets_confirmed_at(api, T):
    with at(9, 41):
        data = patch(api, "24817", {"confirm_initials": "jd"}).json()
    assert data["confirm_initials"] == "JD"
    assert data["confirmed_at"][11:16] == "09:41"


def test_r22_editing_keeps_original_timestamp(api, T):
    with at(9, 41):
        first = patch(api, "24817", {"confirm_initials": "jd"}).json()["confirmed_at"]
    with at(11, 0):
        data = patch(api, "24817", {"confirm_initials": "jdk"}).json()
    assert (data["confirm_initials"], data["confirmed_at"]) == ("JDK", first)


def test_r22_clearing_initials_clears_timestamp(api, T):
    data = patch(api, "24811", {"confirm_initials": ""}).json()
    assert (data["confirm_initials"], data["confirmed_at"]) == ("", None)


# --- R23 notes --------------------------------------------------------------


def test_r23_dispatch_notes_save(api, T):
    data = patch(api, "24817", {"dispatch_notes": "Gate code 4411\nCall on arrival"}).json()
    assert data["dispatch_notes"] == "Gate code 4411\nCall on arrival"
    row = next(r for r in board(api, T)["rows"] if r["display_number"] == "24817")
    assert row["dispatch_notes"] == "Gate code 4411\nCall on arrival"


def test_r23_notes_capped(api, T):
    assert "dispatch_notes" in patch(api, "24817", {"dispatch_notes": "x" * 2001}).json()


# --- R24 / R25 range and trip view ------------------------------------------


def test_r24_range_overlap(api, T):
    data = board(api, T, start=day(T, 3), end=day(T, 3), view="all")
    assert numbers(data) == ["24838"]  # runs T+2 to T+5


def test_r24_end_before_start_rejected(api, T):
    response = api.get("/api/board/", {"start": day(T, 1), "end": day(T)})
    assert response.status_code == 400


def test_r25_today_view(api, T):
    data = board(api, T, start=day(T, 1), view="today")
    assert numbers(data) == ["24826", "24829", "24832", "24844"]


def test_r25_away_view(api, T):
    data = board(api, T, start=day(T, 1), view="away")
    assert numbers(data) == ["24820", "24823-1", "24823-2", "24826"]


def test_r25_all_view(api, T):
    data = board(api, T, start=day(T, 1), view="all")
    assert numbers(data) == [
        "24820",
        "24823-1",
        "24823-2",
        "24826",
        "24829",
        "24832",
        "24844",
    ]


def test_r25_bad_view_rejected(api, T):
    assert api.get("/api/board/", {"view": "week"}).status_code == 400


# --- R26 day labels ---------------------------------------------------------


def test_r26_day_labels_on_board(api, T):
    labels = {
        r["display_number"]: r["day_label"]
        for r in board(api, T, start=day(T, 1), view="all")["rows"]
    }
    assert labels["24829"] == "1/1"
    assert labels["24820"] == "2/3"
    assert labels["24823-1"] == "2/2"
    assert labels["24826"] == "1/2"


def test_r26_range_covering_several_days(api, T):
    rows = board(api, T, start=day(T), end=day(T, 1), view="all")["rows"]
    label = next(r["day_label"] for r in rows if r["display_number"] == "24820")
    assert label == "1–2/3"


@pytest.mark.parametrize(
    ("begin", "ret", "start", "end", "label"),
    [
        (0, 0, 0, 0, "1/1"),
        (0, 2, 1, 1, "2/3"),
        (0, 2, 0, 1, "1–2/3"),
        (0, 2, -5, 9, "1–3/3"),
        (0, 3, 2, 3, "3–4/4"),
    ],
)
def test_r26_day_label(begin, ret, start, end, label):
    base = dt.date(2026, 11, 9)
    c = Contract(begin_date=base + dt.timedelta(begin), return_date=base + dt.timedelta(ret))
    assert day_label(c, base + dt.timedelta(start), base + dt.timedelta(end)) == label


# --- R27 terminal filter ----------------------------------------------------


def test_r27_terminals_omitted_means_all(api, T):
    assert board(api, T)["counts"]["trips"] == 6


def test_r27_terminal_subset(api, T):
    data = board(api, T, terminals="NY")
    assert numbers(data) == ["24820"]
    assert data["counts"]["trips"] == 1


def test_r27_several_terminals(api, T):
    data = board(api, T, terminals="ny,nj")
    assert len(data["rows"]) == 6


def test_r27_empty_means_none(api, T):
    data = board(api, T, terminals="")
    assert data["rows"] == []
    assert data["counts"] == {"trips": 0, "need_driver_or_bus": 0, "pending_confirmation": 0}


# --- R28 search -------------------------------------------------------------


@pytest.mark.parametrize(
    ("q", "expected"),
    [
        ("24823-2", ["24823-2"]),
        ("hoboken youth", ["24811"]),  # organization
        ("u14", ["24811"]),  # group
        ("stevens park", ["24811"]),  # pickup
        ("allentown", ["24811"]),  # destination
        ("3100 lehigh", ["24811"]),  # street address, hidden on the board
        ("marcus", ["24811"]),  # driver
        ("4533", ["24814"]),  # bus number
        ("zzz", []),
    ],
)
def test_r28_board_search(api, T, q, expected):
    assert numbers(board(api, T, q=q)) == expected


def test_r28_search_does_not_change_counts(api, T):
    data = board(api, T, q="marcus")
    assert data["counts"] == {"trips": 6, "need_driver_or_bus": 3, "pending_confirmation": 4}


# --- R29 counts -------------------------------------------------------------


def test_r29_counts(api, T):
    assert board(api, T)["counts"] == {
        "trips": 6,
        "need_driver_or_bus": 3,
        "pending_confirmation": 4,
    }


def test_r29_cancelled_unit_excluded_from_need_and_pending(api, T):
    post(api, "24817", "cancel")
    assert board(api, T)["counts"] == {
        "trips": 6,
        "need_driver_or_bus": 2,
        "pending_confirmation": 3,
    }


def test_r29_assigning_updates_counts(api, T):
    patch(api, "24823-1", {"bus": bus_id("4520")})
    assert board(api, T)["counts"]["need_driver_or_bus"] == 2


# --- R30 sorting ------------------------------------------------------------


def sorted_numbers(api, T, key, direction="asc"):
    return numbers(board(api, T, sort=key, dir=direction))


def test_r30_default_order(api, T):
    assert numbers(board(api, T)) == ["24811", "24814", "24817", "24820", "24823-1", "24823-2"]


def test_r30_contract_descending_keeps_units_together(api, T):
    post(api, "24823-1", "duplicate")
    assert sorted_numbers(api, T, "contract", "desc") == [
        "24823-D1",
        "24823-2",
        "24823-1",
        "24820",
        "24817",
        "24814",
        "24811",
    ]


def test_r30_time_sort_blanks_last_both_ways(api, T):
    # Report times: 24811 04:15, 24814 05:30, 24823-1 10:00; the rest blank.
    asc = sorted_numbers(api, T, "reportTime")
    desc = sorted_numbers(api, T, "reportTime", "desc")
    assert asc[:3] == ["24811", "24814", "24823-1"]
    assert desc[:3] == ["24823-1", "24814", "24811"]
    assert set(asc[3:]) == set(desc[3:]) == {"24817", "24820", "24823-2"}


def test_r30_time_sorts_by_time_of_day(api, T):
    assert sorted_numbers(api, T, "startTime")[0] == "24811"  # 05:30 is earliest


def test_r30_bus_sorts_numerically(api, T):
    # 3108 < 4512 < 4533 numerically.
    assert sorted_numbers(api, T, "busNum")[:3] == ["24820", "24811", "24814"]


def test_r30_size_sorts_numerically(api, T):
    Contract.objects.filter(number=24817).update(size_requirement="28-pax shuttle")
    assert sorted_numbers(api, T, "sizeReq")[0] == "24817"


def test_r30_text_sort(api, T):
    names = [r["driver"] for r in board(api, T, sort="driver")["rows"]]
    filled = [n for n in names if n]
    assert filled == sorted(filled)
    assert names[len(filled) :] == [None] * (len(names) - len(filled))


def test_r30_bad_sort_key_rejected(api, T):
    assert api.get("/api/board/", {"sort": "nope"}).status_code == 400


# --- Unit detail ------------------------------------------------------------


def test_unit_detail_has_panel_fields(api, T):
    data = api.get(f"/api/units/{unit_id('24823-1')}/").json()
    assert data["display_number"] == "24823-1"
    assert data["passengers"] == Contract.objects.get(number=24823).passengers
    assert data["bus_count"] == 2
    assert data["requested_driver_name"] == "Luis Ortega"
    assert data["driver_id"] == Driver.objects.get(name="Luis Ortega").pk
    assert data["bus_id"] is None
    assert {"contact_name", "contact_phone", "info", "itinerary"} <= set(data)


def test_unit_list_and_put_not_available(api, T):
    assert api.get("/api/units/").status_code == 404
    uid = unit_id("24817")
    assert api.put(f"/api/units/{uid}/", {}, content_type="application/json").status_code == 405
    assert api.post("/api/units/", {}, content_type="application/json").status_code in (404, 405)


# --- Excel export -----------------------------------------------------------


def load(response):
    from openpyxl import load_workbook

    assert response.status_code == 200
    return load_workbook(BytesIO(response.content)).active


def test_export_header_and_row_count(api, T):
    response = api.get("/api/board/export.xlsx", {"start": day(T)})
    assert response["Content-Disposition"] == (
        f'attachment; filename="CharterStack-board-{day(T)}.xlsx"'
    )
    ws = load(response)
    header = [c.value for c in ws[1]]
    assert header[:5] == ["Contract #", "Day", "Terminal", "Begin date", "Start time"]
    assert len(header) == 23
    assert ws.max_row == 1 + 6
    assert ws.freeze_panes == "A2"
    assert ws.auto_filter.ref == ws.dimensions
    assert all(c.font.bold for c in ws[1])


def test_export_follows_columns_search_and_sort(api, T):
    ws = load(
        api.get(
            "/api/board/export.xlsx",
            {
                "start": day(T),
                "columns": "driver,contract,busNum,confInit",
                "sort": "contract",
                "dir": "desc",
                "q": "nj",
            },
        )
    )
    rows = [[c.value for c in r] for r in ws.iter_rows()]
    assert rows[0] == ["Driver", "Contract #", "Bus #", "Initials"]
    assert [r[1] for r in rows[1:]] == ["24823-2", "24823-1", "24820", "24817", "24814", "24811"]
    assert rows[1] == ["Unassigned", "24823-2", "Needed", "Pending"]
    assert rows[-1] == ["Marcus Bell", "24811", "#4512", "AR"]


def test_export_formats(api, T):
    ws = load(
        api.get(
            "/api/board/export.xlsx",
            {
                "start": day(T),
                "q": "24811",
                "columns": "beginDate,startTime,returnTime,confAt,hasNotes",
            },
        )
    )
    values = [c.value for c in ws[2]]
    assert values[0] == f"{T:%m/%d/%Y}"
    assert values[1] == "05:30"
    assert values[2] == "19:00"
    assert values[3] is not None and len(values[3]) == len("11/07 10:12")
    assert values[4] is None  # no notes


def test_export_widths(api, T):
    ws = load(
        api.get("/api/board/export.xlsx", {"columns": "contract,notesText", "widths": "140,350"})
    )
    assert ws.column_dimensions["A"].width == 20
    assert ws.column_dimensions["B"].width == 50


def test_export_unknown_column_rejected(api, T):
    assert api.get("/api/board/export.xlsx", {"columns": "contract,bogus"}).status_code == 400


def test_export_no_am_pm(api, T):
    ws = load(api.get("/api/board/export.xlsx", {"start": day(T), "view": "all"}))
    text = " ".join(str(c.value) for row in ws.iter_rows() for c in row if c.value)
    assert " AM" not in text and " PM" not in text


def test_timezone_now_is_patchable():
    with at(5, 28):
        assert timezone.localtime(timezone=NY).strftime("%H:%M") == "05:28"
