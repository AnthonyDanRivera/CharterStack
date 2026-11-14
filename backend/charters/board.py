"""Dispatch board rules (docs/BUSINESS_RULES.md R07, R16-R30).

The board is built in Python from the owner's units: a sandbox holds at most a
few hundred, and the labels, counts and sort rules read more clearly as plain
code than as SQL annotations.
"""

import datetime as dt
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.db.models import Max, QuerySet
from django.utils import timezone

from .models import Bus, Contract, TripUnit
from .timeutil import format_hhmm

VIEWS = ("today", "away", "all")
MAX_DUPLICATES_PER_CONTRACT = 20

# Column keys shared by the board, sorting and the Excel export (docs/API.md).
COLUMNS = [
    "contract", "day", "terminal", "beginDate", "startTime", "reportTime", "actualReport",
    "spotTime", "onLocAt", "org", "pickup", "dest", "group", "driver", "busNum", "sizeReq",
    "returnDate", "returnTime", "confInit", "confAt", "driverPhone", "hasNotes", "notesText",
]  # fmt: skip
COLUMN_LABELS = {
    "contract": "Contract #", "day": "Day", "terminal": "Terminal", "beginDate": "Begin date",
    "startTime": "Start time", "reportTime": "Report time", "actualReport": "Actual report",
    "spotTime": "Spot", "onLocAt": "On location", "org": "Organization", "pickup": "Pickup",
    "dest": "Destination", "group": "Group name", "driver": "Driver", "busNum": "Bus #",
    "sizeReq": "Size req.", "returnDate": "Return date", "returnTime": "Return time",
    "confInit": "Initials", "confAt": "Entered", "driverPhone": "Driver phone",
    "hasNotes": "Notes", "notesText": "Dispatch notes",
}  # fmt: skip
# Default widths in px (docs/UI_GUIDE.md), used to size export columns.
COLUMN_WIDTHS = {
    "contract": 96, "day": 58, "terminal": 86, "beginDate": 86, "startTime": 68,
    "reportTime": 78, "actualReport": 78, "spotTime": 60, "onLocAt": 84, "org": 108,
    "pickup": 122, "dest": 122, "group": 96, "driver": 98, "busNum": 66, "sizeReq": 84,
    "returnDate": 86, "returnTime": 68, "confInit": 70, "confAt": 80, "driverPhone": 104,
    "hasNotes": 56, "notesText": 200,
}  # fmt: skip
TIME_COLUMNS = {"startTime", "reportTime", "actualReport", "spotTime", "onLocAt", "returnTime"}
DATE_COLUMNS = {"beginDate", "returnDate", "confAt"}
NUMBER_COLUMNS = {"busNum", "sizeReq", "day"}


# ---------------------------------------------------------------------------
# Per-unit values
# ---------------------------------------------------------------------------


def effective_status(unit: TripUnit) -> str:
    """R07: a cancelled contract's units always show as cancelled."""
    if unit.contract.status == Contract.Status.CANCELLED:
        return TripUnit.Status.CANCELLED
    return unit.status


def is_cancelled(unit: TripUnit) -> bool:
    """R07/R29: cancelled for counts, either on its own or through its contract."""
    return effective_status(unit) == TripUnit.Status.CANCELLED


def day_label(contract: Contract, start: dt.date, end: dt.date) -> str:
    """R26: which day(s) of the trip fall in the range: `1/1`, `2/3`, `1–2/3`."""
    total = (contract.return_date - contract.begin_date).days + 1
    first = (max(contract.begin_date, start) - contract.begin_date).days + 1
    last = (min(contract.return_date, end) - contract.begin_date).days + 1
    first, last = max(1, first), min(total, last)
    days = str(first) if first >= last else f"{first}–{last}"
    return f"{days}/{total}"


def place_line(location: str, address: str, city: str, state: str, zip_code: str) -> str:
    """Full one-line place: `Union City High School, 2500 Kennedy Blvd, Union City, NJ 07087`."""
    street = ", ".join(p for p in (location.strip(), address.strip()) if p)
    tail = f"{city}, {state}" + (f" {zip_code}" if zip_code else "")
    return f"{street}, {tail}" if street else tail


def pickup_line(c: Contract) -> str:
    """Board Pickup column, also searched by R28."""
    return place_line(
        c.pickup_location, c.pickup_address, c.pickup_city, c.pickup_state, c.pickup_zip
    )


def destination_line(c: Contract) -> str:
    """Board Destination column, also searched by R28."""
    return place_line(c.dest_location, c.dest_address, c.dest_city, c.dest_state, c.dest_zip)


def actual_report_late(unit: TripUnit) -> bool:
    """R19: the actual report time shows red when it is later than the planned report time."""
    return bool(
        unit.actual_report_time and unit.report_time and unit.actual_report_time > unit.report_time
    )


def bus_warnings(contract: Contract, bus: Bus | None) -> list[str]:
    """R18: non-blocking capacity and wheelchair-lift warnings for a bus choice.

    Passengers per bus = ceil(passengers / bus_count); duplicates are not counted.
    """
    if bus is None:
        return []
    warnings = []
    per_bus = math.ceil(contract.passengers / max(1, contract.bus_count))
    if bus.seats < per_bus:
        if contract.bus_count > 1:
            warnings.append(
                f"Bus #{bus.number} seats {bus.seats}; each bus needs about {per_bus} seats."
            )
        else:
            warnings.append(
                f"Bus #{bus.number} seats {bus.seats}; "
                f"this group has {contract.passengers} passengers."
            )
    if contract.needs_wc and not bus.has_wc_lift:
        warnings.append(f"Bus #{bus.number} has no wheelchair lift; this trip needs WC.")
    return warnings


def unit_default_key(unit: TripUnit) -> tuple:
    """R30 default order: contract number, regular units by number, then duplicates (R16)."""
    return (unit.contract.number, unit.is_duplicate, unit.unit_number)


# ---------------------------------------------------------------------------
# Board query
# ---------------------------------------------------------------------------


@dataclass
class BoardQuery:
    start: dt.date
    end: dt.date
    view: str = "today"
    terminals: list[str] | None = None  # None = all; [] = none (R27)
    q: str = ""
    sort: str | None = None
    direction: str = "asc"


def board_units(qs: QuerySet[TripUnit]) -> QuerySet[TripUnit]:
    return qs.select_related(
        "contract", "contract__terminal", "contract__requested_driver", "driver", "bus"
    )


def in_range_and_view(contract: Contract, start: dt.date, end: dt.date, view: str) -> bool:
    """R24 date-range overlap combined with R25 trip view."""
    if not (contract.begin_date <= end and contract.return_date >= start):
        return False
    if view == "away":
        return contract.is_multi_day
    if view == "today":
        return not contract.is_multi_day or start <= contract.begin_date <= end
    return True


def filter_board(units: Iterable[TripUnit], query: BoardQuery) -> list[TripUnit]:
    """R07 (no quotes), R24 range, R25 view and R27 terminal filter. Not the search."""
    out = []
    for unit in units:
        c = unit.contract
        if c.status == Contract.Status.QUOTE:
            continue
        if query.terminals is not None and c.terminal.code not in query.terminals:
            continue
        if in_range_and_view(c, query.start, query.end, query.view):
            out.append(unit)
    return out


def board_counts(units: list[TripUnit]) -> dict[str, int]:
    """R29: counts over the filtered units (before search); cancelled units excluded."""
    live = [u for u in units if not is_cancelled(u)]
    return {
        "trips": len(units),
        "need_driver_or_bus": sum(1 for u in live if u.driver_id is None or u.bus_id is None),
        "pending_confirmation": sum(1 for u in live if not u.confirm_initials),
    }


def matches_search(unit: TripUnit, q: str) -> bool:
    """R28: case-insensitive substring over display number, organization, group,
    pickup, destination, driver name and bus number."""
    q = q.strip().lower()
    if not q:
        return True
    c = unit.contract
    haystack = [
        unit.display_number,
        c.organization,
        c.group_name,
        pickup_line(c),
        destination_line(c),
        unit.driver.name if unit.driver else "",
        unit.bus.number if unit.bus else "",
    ]
    return any(q in value.lower() for value in haystack)


# ---------------------------------------------------------------------------
# Sorting (R30)
# ---------------------------------------------------------------------------


def _leading_number(text: str) -> float | None:
    m = re.match(r"\s*#?(\d+(?:\.\d+)?)", text or "")
    return float(m.group(1)) if m else None


def sort_value(row: dict[str, Any], key: str) -> Any:
    """The comparable value of a board row for a column, or None when blank."""
    value = row.get(SORT_SOURCES.get(key, key))
    if key == "hasNotes":
        return 1 if row["dispatch_notes"] else None
    if key == "confInit":
        return row["confirm_initials"] or None
    if value in (None, ""):
        return None
    if key in TIME_COLUMNS or key in DATE_COLUMNS:
        return value  # HH:MM and ISO strings sort correctly as text
    if key == "busNum":
        return _leading_number(value)
    if key == "sizeReq":
        n = _leading_number(value)
        return (n, value.lower()) if n is not None else None
    if key == "day":
        n = _leading_number(value)
        return n
    return str(value).lower()


SORT_SOURCES = {
    "terminal": "terminal",
    "beginDate": "begin_date",
    "startTime": "start_time",
    "reportTime": "report_time",
    "actualReport": "actual_report_time",
    "spotTime": "spot_time",
    "onLocAt": "on_location_time",
    "org": "organization",
    "pickup": "pickup",
    "dest": "destination",
    "group": "group_name",
    "driver": "driver",
    "busNum": "bus",
    "sizeReq": "size_requirement",
    "returnDate": "return_date",
    "returnTime": "return_time",
    "confAt": "confirmed_at",
    "driverPhone": "driver_phone",
    "notesText": "dispatch_notes",
    "day": "day_label",
}


def sort_rows(rows: list[dict[str, Any]], key: str | None, direction: str) -> list[dict[str, Any]]:
    """R30: default order by contract (units kept together); a column sorts ascending or
    descending, blanks always last, ties kept in default order."""
    rows = sorted(rows, key=lambda r: r["_default"])
    if not key or key not in COLUMNS:
        return rows
    reverse = direction == "desc"
    if key == "contract":
        return sorted(rows, key=lambda r: r["_default"], reverse=reverse)
    filled = [r for r in rows if sort_value(r, key) is not None]
    blank = [r for r in rows if sort_value(r, key) is None]
    # sorted() is stable in both directions, so ties stay in default order.
    filled.sort(key=lambda r: sort_value(r, key), reverse=reverse)
    return filled + blank


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------


def board_row(unit: TripUnit, start: dt.date, end: dt.date) -> dict[str, Any]:
    """One board row (docs/API.md `GET /api/board/`)."""
    c = unit.contract
    confirmed = timezone.localtime(unit.confirmed_at) if unit.confirmed_at else None
    return {
        "id": unit.pk,
        "contract_id": c.pk,
        "contract_number": c.number,
        "display_number": unit.display_number,
        "is_duplicate": unit.is_duplicate,
        "day_label": day_label(c, start, end),
        "is_multi_day": c.is_multi_day,
        "terminal": c.terminal.code,
        "begin_date": c.begin_date.isoformat(),
        "start_time": format_hhmm(c.start_time),
        "spot_time": format_hhmm(c.spot_time),
        "report_time": format_hhmm(unit.report_time),
        "actual_report_time": format_hhmm(unit.actual_report_time),
        "actual_report_late": actual_report_late(unit),
        "on_location_time": format_hhmm(unit.on_location_time),
        "organization": c.organization,
        "group_name": c.group_name,
        "pickup": pickup_line(c),
        "destination": destination_line(c),
        "return_date": c.return_date.isoformat(),
        "return_time": format_hhmm(c.return_time),
        "driver": unit.driver.name if unit.driver else None,
        "driver_phone": unit.driver.phone if unit.driver else None,
        "bus": unit.bus.number if unit.bus else None,
        "bus_seats": unit.bus.seats if unit.bus else None,
        "size_requirement": c.size_requirement,
        "needs_wc": c.needs_wc,
        "confirm_initials": unit.confirm_initials,
        "confirmed_at": confirmed.isoformat(timespec="seconds") if confirmed else None,
        "status": effective_status(unit),
        "dispatch_notes": unit.dispatch_notes,
        "_default": unit_default_key(unit),
    }


def public(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if not k.startswith("_")}


def build_board(qs: QuerySet[TripUnit], query: BoardQuery) -> dict[str, Any]:
    """Everything `GET /api/board/` returns: counts (before search) and sorted rows."""
    units = filter_board(board_units(qs), query)
    counts = board_counts(units)
    rows = [board_row(u, query.start, query.end) for u in units if matches_search(u, query.q)]
    rows = sort_rows(rows, query.sort, query.direction)
    return {
        "counts": counts,
        "refreshed_at": timezone.localtime().isoformat(timespec="seconds"),
        "rows": [public(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# Unit changes (R16, R19-R22)
# ---------------------------------------------------------------------------


def now_hhmm() -> dt.time:
    """Current time in the active (visitor's) time zone, to the minute."""
    return timezone.localtime().time().replace(second=0, microsecond=0)


def toggle_reported(unit: TripUnit, clear: bool = False) -> TripUnit:
    """R19: stamp actual_report_time with now; pressing again (or `clear`) clears it."""
    if clear or unit.actual_report_time is not None:
        unit.actual_report_time = None
    else:
        unit.actual_report_time = now_hhmm()
    unit.save(update_fields=["actual_report_time"])
    return unit


def toggle_on_location(unit: TripUnit) -> TripUnit:
    """R20: set `onloc` and stamp the time; pressing again clears both.

    R21: on location and cancelled are mutually exclusive.
    """
    if unit.status == TripUnit.Status.ON_LOCATION:
        unit.status = TripUnit.Status.NORMAL
        unit.on_location_time = None
    else:
        unit.status = TripUnit.Status.ON_LOCATION
        unit.on_location_time = now_hhmm()
    unit.save(update_fields=["status", "on_location_time"])
    return unit


def toggle_cancelled(unit: TripUnit) -> TripUnit:
    """R21: toggle `cancelled` on this unit only; setting it clears on_location_time."""
    if unit.status == TripUnit.Status.CANCELLED:
        unit.status = TripUnit.Status.NORMAL
    else:
        unit.status = TripUnit.Status.CANCELLED
        unit.on_location_time = None
    unit.save(update_fields=["status", "on_location_time"])
    return unit


def normalize_initials(text: str) -> str:
    """R22: uppercase, letters only, at most 4."""
    return re.sub(r"[^A-Z]", "", (text or "").upper())[:4]


def set_initials(unit: TripUnit, text: str) -> None:
    """R22: first entry sets confirmed_at; editing keeps it; clearing clears it."""
    initials = normalize_initials(text)
    if not initials:
        unit.confirmed_at = None
    elif not unit.confirm_initials or unit.confirmed_at is None:
        unit.confirmed_at = timezone.now()
    unit.confirm_initials = initials


class DuplicateLimitReached(Exception):
    pass


@transaction.atomic
def duplicate_unit(unit: TripUnit, owner: AbstractBaseUser) -> TripUnit:
    """R16: one new blank duplicate on the unit's contract, numbered after the last one."""
    contract = Contract.objects.select_for_update().get(pk=unit.contract_id)
    dups = contract.units.filter(is_duplicate=True)
    if dups.count() >= MAX_DUPLICATES_PER_CONTRACT:
        raise DuplicateLimitReached
    last = dups.aggregate(n=Max("unit_number"))["n"] or 0
    return TripUnit.objects.create(
        owner=owner, contract=contract, is_duplicate=True, unit_number=last + 1
    )


# ---------------------------------------------------------------------------
# Excel export
# ---------------------------------------------------------------------------


def _us_date(iso: str | None) -> str:
    if not iso:
        return ""
    d = dt.date.fromisoformat(iso[:10])
    return f"{d:%m/%d/%Y}"


def export_value(row: dict[str, Any], key: str) -> str:
    """Cell text for the Excel export; blank driver/bus/initials read Unassigned/Needed/Pending."""
    match key:
        case "contract":
            return row["display_number"]
        case "day":
            return row["day_label"]
        case "beginDate":
            return _us_date(row["begin_date"])
        case "returnDate":
            return _us_date(row["return_date"])
        case "driver":
            return row["driver"] or "Unassigned"
        case "busNum":
            return f"#{row['bus']}" if row["bus"] else "Needed"
        case "confInit":
            return row["confirm_initials"] or "Pending"
        case "confAt":
            at = row["confirmed_at"]
            return f"{at[5:7]}/{at[8:10]} {at[11:16]}" if at else ""
        case "hasNotes":
            return "Yes" if row["dispatch_notes"] else ""
        case "returnTime":
            return row["return_time"] or "—"
        case _:
            value = row.get(SORT_SOURCES.get(key, key))
            return "" if value is None else str(value)


def export_workbook(rows: list[dict[str, Any]], columns: list[str], widths: list[int] | None):
    """R-export: bold frozen header row with auto-filter, widths proportional to the board."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Board"
    ws.append([COLUMN_LABELS[c] for c in columns])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append([export_value(row, c) for c in columns])
    for i, key in enumerate(columns):
        px = widths[i] if widths and i < len(widths) else COLUMN_WIDTHS[key]
        ws.column_dimensions[get_column_letter(i + 1)].width = max(6, round(px / 7))
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    return wb


# ---------------------------------------------------------------------------
# Bus board (R34, R35)
# ---------------------------------------------------------------------------


def bus_number_key(number: str) -> tuple:
    """R34: bus numbers sort numerically (`3102` < `4508` < `4512`); text ones after."""
    return (0, int(number), "") if number.isdigit() else (1, 0, number)


def bus_board(units: QuerySet[TripUnit], terminal, start: dt.date, end: dt.date) -> dict[str, Any]:
    """R34/R35: a terminal's active buses, one row per model, with their trips in range.

    `units` must already be scoped to the visitor's sandbox. Rows are ordered by
    seats (largest first) then model name; buses by number, increasing. A bus's
    assignments are its non-quote, non-cancelled units overlapping the range.
    """
    buses = list(Bus.objects.filter(is_active=True, terminal=terminal))
    assigned: dict[int, list[TripUnit]] = {b.pk: [] for b in buses}
    in_range = units.filter(
        bus__in=buses,
        contract__begin_date__lte=end,
        contract__return_date__gte=start,
    ).exclude(contract__status=Contract.Status.QUOTE)
    for unit in in_range.select_related("contract", "driver"):
        if not is_cancelled(unit):
            assigned[unit.bus_id].append(unit)

    rows: dict[str, dict[str, Any]] = {}
    for bus in sorted(buses, key=lambda b: bus_number_key(b.number)):
        trips = sorted(
            assigned[bus.pk], key=lambda u: (u.contract.begin_date, u.contract.start_time)
        )
        row = rows.setdefault(bus.model, {"model": bus.model, "seats": bus.seats, "buses": []})
        row["seats"] = max(row["seats"], bus.seats)
        row["buses"].append(
            {
                "id": bus.pk,
                "number": bus.number,
                "seats": bus.seats,
                "has_wc_lift": bus.has_wc_lift,
                "available": not trips,
                "assignments": [
                    {
                        "unit_id": u.pk,
                        "display_number": u.display_number,
                        "driver": u.driver.name if u.driver else None,
                        "begin_date": u.contract.begin_date.isoformat(),
                        "return_date": u.contract.return_date.isoformat(),
                        "start_time": format_hhmm(u.contract.start_time),
                        "organization": u.contract.organization,
                    }
                    for u in trips
                ],
            }
        )
    ordered = sorted(rows.values(), key=lambda r: (-r["seats"], r["model"]))
    return {
        "terminal": {"code": terminal.code, "name": terminal.name},
        "start": start.isoformat(),
        "end": end.isoformat(),
        "counts": {
            "buses": len(buses),
            "available": sum(1 for r in ordered for b in r["buses"] if b["available"]),
        },
        "rows": ordered,
    }
