# Business Rules

These rules live in the Django backend (model methods, serializers, or a small `services.py`). React only displays the results. Every rule here needs at least one pytest test; rule IDs are for naming tests (`test_r07_quote_hidden_from_board`).

## Times and dates

**R01 — Military time everywhere.** All times are stored as `TimeField` and shown as 24-hour `HH:MM` (`06:45`, `14:15`). No AM/PM anywhere in the UI or API.

**R02 — Smart time input.** Time fields accept loose typing and normalize it. The API accepts and normalizes the same forms, so the rule is tested once in Python (the frontend may also normalize for instant feedback):

| Typed | Result |
|---|---|
| `7`, `07` | `07:00` |
| `730`, `0730`, `7:30` | `07:30` |
| `1915`, `19:15` | `19:15` |
| `7p`, `7 pm`, `7:30PM` | `19:00`, `19:00`, `19:30` |
| `ow`, `one way` (return time only) | One way (null) |
| `25`, `7:75`, `abc` | rejected: "Enter a valid time" |

**R03 — One way.** A null `return_time` means one way. It displays as `One way` in Booking and as a dash on the board. One way does not block or clear the return date; `return_date` is still required (same as `begin_date` for a same-day drop-off).

**R04 — Return on or after begin.** `return_date >= begin_date`. Error text: "Return date can't be before the begin date."

**R05 — Spot before start (new in the build; the prototype does not check this).** `spot_time <= start_time`. Error text: "Spot time can't be after the start time."

## Contracts

**R06 — Contract numbers are assigned by the server.** New contract number = highest existing number for this owner + 1. The form shows the next number read-only. Users never type a contract number.

**R07 — Contract status.**
- `booked` (default): units appear on the dispatch board.
- `quote`: a priced offer the customer has not accepted. **Hidden from the dispatch board entirely.** Visible in Booking.
- `cancelled`: stays on record. Its units stay on the board but always display as cancelled (red row), whatever their own status. They are excluded from the "need driver or bus" and "pending confirmation" counts.

**R08 — Required fields** (asterisk in the form): organization, group name, passengers, contract status, contact name, phone, begin date, spot time, start time, return date, return time (or One way), pickup address, pickup state, pickup city, destination address, destination state, destination city, number of buses, terminal, size requirement, total price. Location names, ZIP, itinerary, requested driver, info, deposit and total paid are optional.

**R09 — ZIP auto-fill.** Entering a known ZIP fills city, state and county. County is read-only and comes only from the ZIP lookup.

**R10 — Delete contract takes three clicks.** "Delete contract" → "Confirm delete?" → "Yes, permanently delete 24817". Deleting removes the contract and all its units. (The API is a plain `DELETE`; the three steps are a UI rule.)

## Pricing

**R11 — Balance due** = `max(0, total_price - total_paid)`. The deposit is a requirement, not money received; it never reduces the balance on its own.

**R12 — Payment status**, first match wins:

| Condition | Status |
|---|---|
| contract is cancelled | `Cancelled` (or `Cancelled · $400.00 kept` when `total_paid > 0`); balance shows `$0.00` |
| `total_price > 0` and `total_paid >= total_price` | `Paid in full` |
| `deposit_required > 0` and `total_paid >= deposit_required` | `Deposit paid` |
| `total_paid > 0` | `Partially paid` |
| otherwise | `Unpaid` |

**R13 — Money validation.** All three amounts are 0 or more. `deposit_required <= total_price`. Input accepts `1200`, `1,200`, `$1,200.00`. Display is always `$1,200.00`.

## Trip units (board rows)

**R14 — Units follow bus count.** Creating a contract creates `bus_count` regular units. Raising `bus_count` adds units at the end. Lowering it removes the highest-numbered regular units first. Duplicates are never touched by bus count changes.

**R15 — Unit display numbers.** Single-bus: `24817`. Multi-bus: `24823-1`, `24823-2`. Duplicate: `24817-D1`. Booking always shows the plain contract number and one entry per contract.

**R16 — Duplicates.** "Duplicate" on the board creates one new duplicate unit for the selected unit's contract, with blank driver, bus, report time, status, confirmation and notes. Duplicating a unit of a multi-bus contract creates exactly one duplicate, not one per bus. Duplicates sort directly after their contract's regular units. "Delete duplicate" is enabled only when a duplicate is selected and takes two clicks ("Delete duplicate" → "Click again to delete"). Duplicates have a blue row background.

**R17 — Assignment.** Assign sets driver, bus and report time on one unit together. Any of the three may be blank. Reset reverts the unsaved dropdown choices to the saved values.

**R18 — Capacity and lift warnings (non-blocking).** When a bus is chosen, the API response includes warnings; the UI shows the first one as a small orange note under the Bus dropdown. Assignment is still allowed.
- Too small: bus seats < passengers per bus, where passengers per bus = `ceil(passengers / bus_count)`. Text: "Bus #3108 seats 35; this group has 48 passengers." (multi-bus: "…; each bus needs about 28 seats.")
- No lift: the contract's size requirement ends in `WC` and the bus has no lift. Text: "Bus #4512 has no wheelchair lift; this trip needs WC."

**R19 — Reported.** The Reported button stamps `actual_report_time` with the current local time, to the minute. Pressing it again clears it. The button label becomes "Reported 05:28" when set. The time shows red when it is later than `report_time`.

**R20 — On location.** The On location button sets `status = onloc` and stamps `on_location_time` with the current time. Pressing it again clears both. Row turns green. The On location time is always black.

**R21 — Cancelled (unit).** The Cancelled button toggles `status = cancelled` on the selected unit only. Setting it clears `on_location_time`. Row turns red. `onloc` and `cancelled` are mutually exclusive.

**R22 — Confirmation initials.** Typing in the Initials cell uppercases, strips non-letters, and keeps at most 4 characters. The first time initials are entered the server sets `confirmed_at` to now; editing the initials keeps the original timestamp; clearing the initials clears the timestamp. "Entered" shows as `MM/DD HH:MM`.

**R23 — Dispatch notes** save as the user types (debounced PATCH). A unit with notes shows a checked square in the Notes column and the note text in the Dispatch notes column.

## Board filtering and counts

**R24 — Date range.** A unit is in range when its contract's `[begin_date, return_date]` overlaps `[range_start, range_end]`. The range defaults to today/today. Previous/next shift the range by its own length. The range is shared by the Dispatch board and Booking tabs.

**R25 — Trip view.**
- **Today trips** (default): single-day trips in range, plus multi-day trips whose **begin date** is in range.
- **Away trips**: only multi-day trips overlapping the range (buses that are out on the road).
- **All trips**: everything overlapping the range.

**R26 — Day column.** Shows which day(s) of the trip fall in the range: `1/1` for a single-day trip, `2/3` for day 2 of a 3-day trip, `1–2/3` when the range covers days 1 to 2.

**R27 — Terminal filter.** Five checkboxes plus "All terminals". All are checked by default. "All terminals" checks every box when it is off and clears every box when it is on. Unchecking any terminal unchecks "All terminals"; re-checking the last one checks it again. With nothing checked the board is empty and the button reads `Terminal: None`.

**R28 — Search.** Case-insensitive substring match over unit display number, organization, group name, pickup, destination, driver name and bus number. Booking search matches contract number, organization, group, contact name, phone, pickup and destination city and location name.

**R29 — Status bar counts** are computed over the units currently in the date range, trip view and terminal filter (not the search):
- trips = number of units
- need driver or bus = units with no driver or no bus, excluding cancelled
- pending confirmation = units with no initials, excluding cancelled

**R30 — Sorting.** Default order is by contract number, with a contract's units kept together (regular units by number, then duplicates). Clicking a column header sorts by that column ascending; clicking the same header again reverses it. Blank values always sort last in either direction. Time columns sort by time of day, date columns by date, Bus # and Size req. numerically, everything else as text.

**R31 — Contract lookup.** Booking's lookup box accepts digits, `D` and `-` (so `24823-2` and `24817-D1` both resolve to their contract). An exact contract number match opens that contract. No match shows "No contract 99999 found."

## Booking list

**R32 — Contract list filter.** All contracts, Active contracts (not cancelled), Booked, Quotes, Cancelled. Combined with the shared date range and the search box.

**R33 — Booking status bar** shows: number of contracts, booked, quotes, cancelled, and total balance due across the listed contracts (cancelled contracts contribute $0).

## Bus board

**R34 — Fleet layout.** The Bus board shows one terminal at a time: the active buses whose home terminal is that terminal. Buses are grouped into one row per bus model. Rows are ordered by seats, largest first (coaches, then minicoaches, then shuttles), then by model name. Within a row, buses are ordered by bus number, numerically increasing from left to right (`3102` before `3121`, `4508` before `4512`). Inactive buses and buses with no home terminal are not shown.

**R35 — Bus assignments.** For the shared date range, each bus lists the trip units it is assigned to whose contract's `[begin_date, return_date]` overlaps the range (same overlap as R24), ordered by begin date and start time. Quotes are never listed (R07), and cancelled units (by their own status or their contract's, R07) do not count, since the bus is free. A bus with no listed trips is **Available**. The status line counts buses and available buses for the terminal. Assignments only ever come from the visitor's own sandbox.
