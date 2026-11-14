"""Generate seed/seed_demo.json: the sample data each demo visitor gets.

Run from the repo root:  python seed/generate_demo.py

Deterministic (fixed random seed), so the output only changes when this file
does. It starts from seed/seed_test.json (the 12 hand-written contracts tests
rely on), then adds a fuller fleet, more drivers and about 45 more contracts
spread around the base day so today's board looks like a real dispatch day.
Dispatch data respects the obvious rules: a bus comes from the contract's
terminal, is big enough and has a lift when the trip needs WC, and no driver or
bus is used twice on overlapping days.
"""

from __future__ import annotations

import datetime as dt
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
RNG = random.Random(20261109)

BASE = dt.date(2026, 11, 9)
WEEKDAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# --- Reference data --------------------------------------------------------

EXTRA_DRIVERS = [
    ("Carlos Reyes", "201"), ("Janet Okafor", "973"), ("Mike Brennan", "732"),
    ("Tanya Brooks", "201"), ("Victor Santos", "551"), ("Hector Ramirez", "201"),
    ("Lisa Chen", "973"), ("Darnell Hayes", "201"), ("Frank DeLuca", "732"),
    ("Monique Price", "862"), ("Steve Novak", "201"), ("Angela Russo", "973"),
    ("Paul Fitzgerald", "908"), ("Rosa Alvarez", "201"), ("James Whitfield", "551"),
    ("Nina Patel", "732"), ("Eddie Morales", "201"), ("Grace Kim", "973"),
    ("Tony Marino", "908"), ("Keisha Johnson", "862"),
]  # fmt: skip

# (number, seats, model, has_wc_lift, terminal); the first 8 are the test fleet.
EXTRA_BUSES = [
    ("4508", 56, "MCI J4500", False, "NJ"), ("4515", 56, "MCI J4500", False, "NJ"),
    ("4527", 57, "Prevost H3-45", True, "NJ"), ("4538", 56, "Van Hool CX45", False, "NJ"),
    ("4552", 56, "Van Hool CX45", False, "NJ"), ("3102", 35, "Minicoach", False, "NJ"),
    ("3121", 35, "Minicoach", True, "NJ"), ("2211", 28, "Shuttle", False, "NJ"),
    ("4604", 56, "MCI J4500", False, "NY"), ("4611", 56, "MCI J4500", False, "NY"),
    ("4619", 57, "Prevost H3-45", True, "NY"), ("4626", 56, "Van Hool CX45", False, "NY"),
    ("4633", 56, "Van Hool CX45", False, "NY"), ("3134", 35, "Minicoach", False, "NY"),
    ("2219", 28, "Shuttle", True, "NY"),
    ("4705", 56, "MCI J4500", False, "PA"), ("4712", 56, "MCI J4500", False, "PA"),
    ("4720", 57, "Prevost H3-45", True, "PA"), ("4731", 56, "Van Hool CX45", False, "PA"),
    ("3140", 35, "Minicoach", False, "PA"), ("2224", 28, "Shuttle", False, "PA"),
    ("4803", 56, "MCI J4500", False, "CT"), ("4810", 57, "Prevost H3-45", True, "CT"),
    ("4818", 56, "Van Hool CX45", False, "CT"), ("3147", 35, "Minicoach", False, "CT"),
    ("2230", 28, "Shuttle", False, "CT"),
    ("4902", 56, "MCI J4500", False, "MA"), ("4909", 57, "Prevost H3-45", True, "MA"),
    ("4917", 56, "Van Hool CX45", False, "MA"), ("3153", 35, "Minicoach", False, "MA"),
    ("2236", 28, "Shuttle", False, "MA"),
]  # fmt: skip

# --- Contract ingredients ---------------------------------------------------

ORGS = [
    ("Jersey City Public Schools", "8th Grade Science Trip", "NJ"),
    ("Paterson Catholic Youth Ministry", "Retreat Weekend", "NJ"),
    ("Montclair State University", "Athletics Department", "NJ"),
    ("Hudson County Seniors Club", "Casino Day Trip", "NJ"),
    ("Newark Arts Collective", "Museum Tour", "NJ"),
    ("Bayonne Little League", "Regional Tournament", "NJ"),
    ("Edison Township Recreation", "Fall Festival Shuttle", "NJ"),
    ("St. Joseph's Church", "Pilgrimage", "NJ"),
    ("Rutgers Alumni Association", "Homecoming Game", "NJ"),
    ("Liberty Health Systems", "Staff Appreciation Outing", "NJ"),
    ("Brooklyn Tech High School", "Senior Class Trip", "NY"),
    ("Queens Borough Choir", "Holiday Concert Tour", "NY"),
    ("Westchester Rotary Club", "Leadership Summit", "NY"),
    ("Albany Medical Center", "Conference Transfer", "NY"),
    ("Staten Island Ferry Fans Club", "City Tour", "NY"),
    ("Penn State Hillel", "Shabbaton", "PA"),
    ("Philadelphia Youth Orchestra", "Competition Travel", "PA"),
    ("Lancaster Mennonite School", "Washington Field Trip", "PA"),
    ("Pittsburgh Steelers Booster Club", "Away Game", "PA"),
    ("Allentown Chamber of Commerce", "Business Expo", "PA"),
    ("Yale Glee Club", "Concert Weekend", "CT"),
    ("Stamford Corporate Events", "Client Golf Outing", "CT"),
    ("Hartford Public Library", "Author Event Shuttle", "CT"),
    ("New Haven Lions Club", "Charity Gala", "CT"),
    ("Boston College Rowing", "Head of the Schuylkill", "MA"),
    ("Cambridge Seniors Center", "Foliage Tour", "MA"),
    ("Fenway Park Tours Group", "Stadium Visit", "MA"),
    ("Hoboken Moms Network", "Pumpkin Patch Trip", "NJ"),
    ("Union County College", "Career Fair", "NJ"),
    ("Kean University Greek Life", "Formal", "NJ"),
    ("Princeton Theological Seminary", "Field Study", "NJ"),
    ("Toms River Fire Company", "Annual Banquet", "NJ"),
    ("Secaucus Business Association", "Networking Mixer", "NJ"),
    ("Clifton High School Band", "Marching Competition", "NJ"),
    ("Morristown Medical Center", "Shift Shuttle", "NJ"),
    ("Fort Lee Korean Church", "Fellowship Picnic", "NJ"),
    ("Elizabeth Youth Soccer", "State Cup", "NJ"),
    ("Weehawken Rotary", "Spring Gala", "NJ"),
    ("Wayne Township Seniors", "Atlantic City Day", "NJ"),
    ("Long Branch Surf Club", "Beach Cleanup", "NJ"),
    ("Hackensack Meridian Health", "Board Retreat", "NJ"),
    ("North Bergen High School", "Prom Transportation", "NJ"),
    ("Passaic County Veterans", "Memorial Visit", "NJ"),
    ("Englewood Hospital", "Nurses Conference", "NJ"),
]

FIRST = ["Maria", "John", "Linda", "Robert", "Patricia", "David", "Jennifer", "Michael",
         "Susan", "William", "Karen", "Joseph", "Nancy", "Thomas", "Lisa", "Daniel",
         "Carmen", "Kevin", "Angela", "Brian", "Diane", "Anthony", "Rachel", "Mark"]  # fmt: skip
LAST = ["Garcia", "Smith", "Johnson", "Lee", "Martinez", "Brown", "Davis", "Lopez",
        "Wilson", "Anderson", "Thomas", "Moore", "Jackson", "Martin", "Thompson", "White",
        "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young"]  # fmt: skip  # noqa: E501

STREETS = ["Main St", "Park Ave", "Broad St", "Washington St", "Market St", "Bergen Ave",
           "Kennedy Blvd", "Central Ave", "Elm St", "River Rd", "Church St", "Union Ave",
           "Ocean Ave", "Grove St", "Summit Ave", "Palisade Ave"]  # fmt: skip
PICKUP_PLACES = ["High School", "Middle School", "Community Center", "Senior Center",
                 "Public Library", "Town Hall", "Church", "Recreation Center", "YMCA", ""]  # fmt: skip  # noqa: E501
DEST_PLACES = ["Convention Center", "Stadium", "Museum", "Arena", "Performing Arts Center",
               "Hotel", "Conference Center", "State Park", "University", "Casino", ""]  # fmt: skip
INFO = [
    "Driver checks in at the front office on arrival.",
    "Coolers allowed under the bus; no food on board.",
    "Group leader rides up front and has the passenger list.",
    "Luggage for all passengers; use all bays.",
    "Two wheelchair users; secure chairs before departure.",
    "Stop for a 20-minute rest break on the way.",
    "Park in the bus lot behind the venue.",
    "Children under 12 on board; seat belts required.",
    "Return time may run late; driver should wait.",
    "",
    "",
]

SIZES = {
    "56-pax coach": (56, "56"), "57-pax coach": (57, "57"),
    "35-pax minicoach": (35, "35"), "28-pax shuttle": (28, "28"),
}  # fmt: skip
INITIALS = ["AR", "MK", "JT", "LP", "DS"]
AREAS = ["201", "973", "732", "908", "212", "718", "215", "203", "617"]


def pick_weighted(pairs):
    total = sum(w for _, w in pairs)
    r = RNG.uniform(0, total)
    for value, w in pairs:
        r -= w
        if r <= 0:
            return value
    return pairs[-1][0]


def hhmm(minutes: int) -> str:
    minutes = max(0, min(minutes, 23 * 60 + 45))
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def short_date(d: dt.date) -> str:
    return f"{WEEKDAY[d.weekday()]} {d:%m/%d}"


def money(amount: float) -> int:
    return int(round(amount / 50.0) * 50)


def main() -> None:
    data = json.loads((HERE / "seed_test.json").read_text(encoding="utf-8"))
    data["_note"] = (
        "CharterStack demo seed, generated by seed/generate_demo.py (do not edit by hand). "
        "Field names match docs/DATA_MODEL.md. Dates are YYYY-MM-DD around base_date; "
        "seed_sandbox() shifts them so base_date becomes today. unit1 holds the dispatch data "
        "for unit 1 of a contract. Tests use the smaller seed/seed_test.json."
    )

    # Reference data: test fleet + extras.
    def phone(area: str, i: int) -> str:
        return f"({area}) 555-{200 + i:04d}"

    data["drivers"] += [{"name": n, "phone": phone(a, i)} for i, (n, a) in enumerate(EXTRA_DRIVERS)]
    data["buses"] += [
        {"number": n, "seats": s, "model": m, "has_wc_lift": wc, "terminal": t}
        for n, s, m, wc, t in EXTRA_BUSES
    ]
    zips_by_state: dict[str, list[tuple[str, list[str]]]] = {}
    for z, v in data["zip_lookup"].items():
        zips_by_state.setdefault(v[1], []).append((z, v))

    # Track who/what is already booked on each day (from the hand-written contracts too).
    busy_driver: dict[dt.date, set[str]] = {}
    busy_bus: dict[dt.date, set[str]] = {}

    def days(begin: dt.date, end: dt.date):
        return [begin + dt.timedelta(n) for n in range((end - begin).days + 1)]

    for c in data["contracts"]:
        u = c["unit1"]
        for d in days(
            dt.date.fromisoformat(c["begin_date"]), dt.date.fromisoformat(c["return_date"])
        ):
            if u["driver"]:
                busy_driver.setdefault(d, set()).add(u["driver"])
            if u["bus"]:
                busy_bus.setdefault(d, set()).add(u["bus"])

    buses = data["buses"]
    drivers = [d["name"] for d in data["drivers"]]
    number = max(c["number"] for c in data["contracts"]) + 2

    # Day plan: how many new contracts begin on each offset from the base day.
    plan = {
        -6: 2,
        -5: 2,
        -4: 2,
        -3: 2,
        -2: 2,
        -1: 3,
        0: 15,
        1: 5,
        2: 4,
        3: 3,
        4: 2,
        5: 2,
        6: 1,
        8: 1,
    }
    orgs = ORGS[:]
    RNG.shuffle(orgs)

    for offset, count in plan.items():
        for _ in range(count):
            # Each organization has a home state; its terminal and pickup city follow.
            org, group, state = orgs.pop() if orgs else RNG.choice(ORGS)
            terminal = state
            pz, pv = RNG.choice(zips_by_state[state])
            dz, dv = RNG.choice(
                [zv for s in zips_by_state for zv in zips_by_state[s] if zv[1][0] != pv[0]]
            )

            size = pick_weighted([("56-pax coach", 50), ("57-pax coach", 15),
                                  ("35-pax minicoach", 22), ("28-pax shuttle", 13)])  # fmt: skip
            seats = SIZES[size][0]
            wc = RNG.random() < 0.12
            bus_count = pick_weighted([(1, 80), (2, 15), (3, 5)])
            per_bus = RNG.randint(max(10, seats // 2), seats)
            passengers = per_bus * bus_count if bus_count > 1 else per_bus

            begin = BASE + dt.timedelta(offset)
            multi = RNG.random() < 0.15
            ret = begin + dt.timedelta(RNG.randint(1, 3)) if multi else begin
            spot = RNG.randrange(5 * 4, 15 * 4) * 15
            start = spot + 30
            one_way = not multi and RNG.random() < 0.08
            back = (
                None
                if one_way
                else hhmm(
                    start + RNG.randrange(6 * 4, 12 * 4) * 15
                    if not multi
                    else RNG.randrange(14 * 4, 21 * 4) * 15
                )
            )

            status = "booked"
            roll = RNG.random()
            if offset >= 2 and roll < 0.12:
                status = "quote"
            elif roll < 0.07:
                status = "cancelled"

            hours = ((ret - begin).days + 1) * (10 if multi else 0) + (0 if one_way else 8)
            price = money(bus_count * (650 + hours * 110 + RNG.randint(0, 600)))
            deposit = money(price * 0.2) if RNG.random() < 0.7 else 0
            paid_kind = RNG.random()
            paid = (
                price
                if paid_kind < 0.35
                else deposit
                if paid_kind < 0.65
                else money(price * 0.5)
                if paid_kind < 0.8
                else 0
            )
            if status == "quote":
                paid = 0

            # Dispatch data for every bus on the contract (seed key "units").
            # Today and earlier are mostly worked; further out is mostly still open.
            near = offset <= 0
            assign_chance = 0.98 if near else 0.7 if offset == 1 else 0.35
            fill = 0.97 if near else 0.85  # chance each of bus / driver is set
            confirm_chance = 0.75 if near else 0.5
            units = []
            span = days(begin, ret)
            for _n in range(bus_count):
                u = {
                    "driver": None,
                    "bus": None,
                    "report_time": None,
                    "confirm_initials": "",
                    "confirmed_at": None,
                }
                if status == "booked" and RNG.random() < assign_chance:
                    fits = [b for b in buses
                            if b["terminal"] == terminal and b["seats"] >= per_bus
                            and (b["has_wc_lift"] or not wc)
                            and not any(b["number"] in busy_bus.get(d, set()) for d in span)]  # fmt: skip  # noqa: E501
                    free = [
                        d for d in drivers if not any(d in busy_driver.get(x, set()) for x in span)
                    ]
                    # Leave some trips needing a bus or a driver, as on a real board.
                    bus = (
                        min(fits, key=lambda b: b["seats"])
                        if fits and RNG.random() < fill
                        else None
                    )
                    driver = RNG.choice(free) if free and RNG.random() < fill else None
                    for d in span:
                        if bus:
                            busy_bus.setdefault(d, set()).add(bus["number"])
                        if driver:
                            busy_driver.setdefault(d, set()).add(driver)
                    u["bus"] = bus["number"] if bus else None
                    u["driver"] = driver
                    if bus or driver:
                        u["report_time"] = hhmm(spot - 45) if RNG.random() < 0.85 else None
                        if RNG.random() < confirm_chance:
                            u["confirm_initials"] = RNG.choice(INITIALS)
                            when = begin - dt.timedelta(RNG.randint(1, 6))
                            u["confirmed_at"] = (
                                f"{when.isoformat()}T{hhmm(RNG.randrange(8 * 4, 18 * 4) * 15)}"
                            )
                units.append(u)

            pick_place = RNG.choice(PICKUP_PLACES)
            dest_place = RNG.choice(DEST_PLACES)
            itinerary = ""
            if multi:
                itinerary = "\n".join([
                    f"{short_date(begin)}  {hhmm(start)}  Depart – {pv[0]}",
                    f"{short_date(begin)}  {hhmm(start + 240)}  Arrive – {dv[0]}",
                    f"{short_date(ret)}  {back}  Return – {pv[0]}",
                ])  # fmt: skip
            first, last = RNG.choice(FIRST), RNG.choice(LAST)

            data["contracts"].append({
                "number": number,
                "status": status,
                "organization": org,
                "group_name": group,
                "passengers": passengers,
                "contact_name": f"{first} {last}",
                "contact_phone": f"({RNG.choice(AREAS)}) 555-{RNG.randint(300, 999):04d}",
                "begin_date": begin.isoformat(),
                "spot_time": hhmm(spot),
                "start_time": hhmm(start),
                "return_date": ret.isoformat(),
                "return_time": back,
                "pickup_location": f"{pv[0]} {pick_place}".strip() if pick_place else "",
                "pickup_address": f"{RNG.randint(10, 2999)} {RNG.choice(STREETS)}",
                "pickup_city": pv[0],
                "pickup_state": pv[1],
                "pickup_zip": pz,
                "dest_location": f"{dv[0]} {dest_place}".strip() if dest_place else "",
                "dest_address": f"{RNG.randint(10, 2999)} {RNG.choice(STREETS)}",
                "dest_city": dv[0],
                "dest_state": dv[1],
                "dest_zip": dz,
                "itinerary": itinerary,
                "bus_count": bus_count,
                "terminal": terminal,
                "size_requirement": f"{size} WC" if wc else size,
                "requested_driver": RNG.choice(drivers) if RNG.random() < 0.25 else None,
                "info": RNG.choice(INFO),
                "total_price": price,
                "deposit_required": deposit,
                "total_paid": paid,
                "units": units,
            })  # fmt: skip
            number += RNG.randint(2, 4)

    out = HERE / "seed_demo.json"
    out.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )

    # Report what today's board will look like.
    today = [c for c in data["contracts"] if c["status"] != "quote" and (
        c["begin_date"] == BASE.isoformat())]  # fmt: skip
    units = sum(c["bus_count"] for c in today)
    print(f"{len(data['contracts'])} contracts, {len(data['drivers'])} drivers, "
          f"{len(data['buses'])} buses; today's board: {units} trips")  # fmt: skip


if __name__ == "__main__":
    main()
