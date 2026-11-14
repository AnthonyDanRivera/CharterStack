# UI Guide — how CharterStack should look and behave

The source of truth for the look is the prototype in `design/Main.dc.html` and the screenshots in `design/screenshots/`. This guide describes every part in words so nothing has to be guessed.

**About the prototype file.** `Main.dc.html` is a design-tool format, not a normal web page. Read it as a reference:
- The `<style>` block inside `<helmet>` holds all the CSS. Later rules override earlier ones (the file was restyled several times), so **the last matching rule wins**. Reuse the final values.
- The markup uses `{{name}}` placeholders, `<sc-for>` loops and `<sc-if>` conditions. Treat it as a template showing structure and class names.
- The `<script>` holds a `Component` class whose `renderVals()` contains the prototype's logic and sample data. Use it to check behavior, but implement the rules in Django per `BUSINESS_RULES.md`.
- Do not copy the prototype's architecture (one giant component, state overrides). Build normal React components.

## Overall look

**No decorative icons.** Buttons and tabs are text only. The few glyphs that are the control itself are custom-drawn in the logo's style (solid shapes, rounded corners), not stock line icons: small filled carets for the ‹ › previous/next and month arrows and the ▾ on dropdowns, and a three-bar grip (echoing the logo's staggered bars) on paired column headers.

A dense, desktop internal tool: closer to a real TMS than a modern marketing app. Plain, small text, thin borders, no cards with big shadows, no badges or pills, no emoji.

| Token | Value |
|---|---|
| Font | `'Segoe UI', Tahoma, Arial, sans-serif`, base 12px; table text 12.5px |
| Monospace (contract numbers) | `Consolas, 'Courier New', monospace` |
| Page background | `#E9EDF2` with a light dot grid: 1.2px dots `rgba(31, 58, 95, 0.24)` every 16px, fixed while scrolling. Never behind table text, only behind the surfaces. |
| Surface (panels, table) | `#FFFFFF`, border `1px solid #C7CFD9`, radius 8px, soft shadow `0 1px 2px rgba(16,24,40,.06), 0 8px 24px rgba(16,24,40,.08)` so it lifts off the dotted background |
| Toolbar and action bar / table header row | `#EEF3F9` (faint blue-grey) / `#E8EDF3`, so controls, headers and trip rows read as separate bands |
| App header bar | `#1F3A5F`, white text |
| Text | `#1B1F24`; secondary `#4A525D`; muted `#5B6470`; placeholder dash `#8E97A3` |
| Primary blue (buttons, focus, Trip information tabs) | `#2F6BC0`; hover `#2759A3`; active inner-tab text `#1A4C8C` |
| Red (warnings, Unassigned, Needed, counts) | `#C0261B` |
| Row: selected | 2px inset outline `#3A424D` |
| Row: duplicate | background `#E2EDFC` |
| Row: on location | solid dark green `#2E7D4F`, white text |
| Row: cancelled | solid dark red `#B3261E`, white text |
| Capacity/lift note | text `#8F3B06` on `#FDEBDD` |
| Inputs and buttons | height 30px (toolbar buttons 28px), radius 4px, border `#BFC7D1` |

Times are 24-hour `HH:MM`. Board dates are `MM/DD/YYYY` with no weekday. Empty values show an em dash in muted grey.

## Page frame (both tabs)

Top to bottom:

1. **Header bar with tabs** — one dark navy bar (`#1F3A5F`, 52px tall). On the left: the CharterStack logo (28px mark, 19px wordmark) (a blue `#2F6BC0` rounded square with three staggered white bars, like rows on a board) and "CharterStack" in bold white, then a thin divider, then the two tabs "Dispatch board" and "Booking". Tabs are white text at 75% opacity on the navy. The active tab inverts: a white rectangle (28px tall, 4px radius, centered in the bar) with navy `#1F3A5F` semi-bold text. Hover on an inactive tab brings it to full white with a faint light background. (Changed from separate header and tab rows to save vertical space for the trip table; the screenshots in `design/screenshots/` still show the old two-row frame.)
2. **Tab content** (below).
3. **Session strip** — a thin grey bar at the very bottom of the page, small text, label in grey then value:
   `Date Thu 11/12/2026 · Time 21:04:37 · User Demo User · Terminal All · Session DEMO-8F3K2 · Session time 00:12:45 · Server demo-server`
   - Date and Time are the visitor's real local date and time; Time ticks every second.
   - Terminal mirrors the board's terminal filter (`All`, `None`, or `NJ, PA`).
   - Session is the demo sandbox's short ID. Session time counts up from login.

## Dispatch board tab

See `design/screenshots/01-dispatch-board.png`. Two white surfaces on the dotted page background, 16px apart: the board (toolbar, status bar, trip table, action bar), then the trip detail area as its own surface below it.

### Toolbar (left to right)
- **‹** previous period button.
- **Start date / End date** — one bordered control with two halves, each a small grey label over a bold date (`Mon, Nov 9, 2026`), separated by a dash. Clicking either half opens the calendar popover below it.
  - Calendar: month title with ‹ › arrows, a one-line hint ("Pick a date to go to it" for Start, "Pick the last date of the range" for End), a 7-column day grid, and a "Today" link. Days in the selected range are tinted; the range ends are solid blue.
  - Picking a start date after the current end sets both to that day. For a single-day selection the End date shows the same date as the Start date.
- **›** next period button, then a **Today** button.
- Vertical separator.
- **Terminal: All ▾** — opens a popover titled "Show terminals" with an "All terminals" checkbox, a divider, five checkboxes (`NJ – New Jersey`, `NY – New York`, `PA – Pennsylvania`, `CT – Connecticut`, `MA – Massachusetts`) and a "Done" button. Behavior: rule R27.
- **Today trips ▾** — dropdown with Today trips, Away trips, All trips (rule R25).
- Pushed to the far right: small grey text `Refreshed 11/12 21:04`, then a **Refresh** button. Refresh refetches the board and updates the time.

All popovers close when the user clicks anywhere outside them. Only one is open at a time.

### Status bar
A white row directly under the toolbar.
- Left: three counts in 15px semi-bold with 17px bold numbers: **6** trips · **3** need driver or bus · **4** pending confirmation. The second and third numbers are red.
- Right: search box, 300px, placeholder "Search contract, org, group, driver…".

### Trip table
A CSS grid with a sticky header, horizontally scrollable when columns exceed the width. Thin vertical lines between all columns and horizontal lines between rows.

**Columns, default order and default widths (px):**

| # | Column | Width | Notes |
|---|---|---|---|
| 1 | Contract # | 96 | Monospace, **bold black**. Unit display number (`24823-1`, `24817-D1`). |
| 2 | Day | 58 | `1/1`, `2/3` (rule R26) |
| 3 | Terminal | 86 | Two-letter code |
| 4 | **Begin date / start time** (pair) | 86 + 68 | Begin date `11/09/2026`; Start time `07:15` |
| 5 | Report time | 78 | Planned report time or dash |
| 6 | Actual report | 78 | Stamped time; red when later than report time. Cleared by pressing Reported again. |
| 7 | Spot | 60 | |
| 8 | On location | 84 | Stamped time, always black, or dash |
| 9 | Organization | 108 | |
| 10 | **Pickup / Destination** (pair) | 122 + 122 | Full text: `Union City High School, 2500 Kennedy Blvd, Union City, NJ 07087`. Wraps. |
| 11 | Group name | 96 | |
| 12 | Driver | 98 | Name, or **Unassigned** in red |
| 13 | **Bus # / Size req.** (pair) | 66 + 84 | Bus: `#4512` with `56 seats` in small grey under it, or **Needed** in red. Size: `56-pax coach`, with **WC** in bold when a lift is needed. |
| 14 | **Return date / time** (pair) | 86 + 68 | `11/10/2026` and `20:00`; dash for one way |
| 15 | **Confirmation** (pair) | 70 + 80 | Initials: a small text input, placeholder "Add". Entered: `11/04 10:12`. |
| 16 | Driver phone | 104 | Assigned driver's phone or dash |
| 17 | Notes | 56 | A small square: checked when the unit has dispatch notes |
| 18 | Dispatch notes | 200 | The note text, muted, wraps |

Columns 1 to 13 fit in a 1440px window without scrolling.

**Paired columns** have a group label on a top header row ("Pickup / Destination") spanning two sub-columns separated by a dashed line. Single columns span both header rows.

**Header behavior:**
- Click a header to sort; click again to reverse. A small up/down arrow shows the direction.
- Drag the right edge of a header to resize (each column has a minimum width).
- Hold and drag a header to move the column; other columns shift live as the dragged one passes their midpoint. A pair moves together and is dragged by its top group label.
- Header text is 12px semi-bold grey and wraps only at spaces.
- "Reset columns" (bottom right of the table) restores the default order and widths. Column order and widths are remembered per browser in localStorage.

**Row behavior:**
- Row text is regular weight (only the contract number, WC, and the red Unassigned/Needed labels stand out).
- Clicking anywhere in a row selects it, including empty cells. Focusing the Initials input also selects the row.
- Selected row: dark 2px inset outline, no fill change. Hover: very light grey.
- Row backgrounds by state: duplicate = light blue; on location = dark green with white text; cancelled = dark red with white text. Status color wins over duplicate color. On those dark rows, labels that are red elsewhere (Unassigned, Needed, a late actual report) turn bold white, secondary grey text turns translucent white, the initials input and notes checkbox turn see-through with white text and a faint white border (solid white only while typing in the input), and a selected row gets a white inset outline instead of the dark one.
- Empty state: "No trips match these dates or search."

### Action bar (under the table)
Left group, all disabled when no row is selected:
- **Reported** — toggles the actual report stamp; label becomes "Reported 05:28" and the button tints blue when set.
- **On location** — always solid dark green `#2E7D4F` with white text; toggles. When on, it turns a darker green `#1F5C39` with a white inset ring. Faded (45% opacity) when no trip is selected.
- **Cancelled** — always solid dark red `#B3261E` with white text; toggles. When on, it turns a darker red `#851A14` with a white inset ring. Faded (45% opacity) when no trip is selected.
- **Duplicate**.
- **Delete duplicate** — enabled only for a selected duplicate; first click turns it red and reads "Click again to delete".
- Separator, then **Export to Excel** — downloads `CharterStack-board-YYYY-MM-DD.xlsx` with the rows currently shown, in the current column order and sort, bold frozen header row with filters. Blank driver/bus/initials export as `Unassigned`, `Needed`, `Pending`.

Right: **Reset columns**.

### Trip detail area (under the action bar)
Two panels side by side: Trip information (about 75% width) and Assign driver & bus (about 25%). With nothing selected: "Select a trip above to see its details and assign a driver and bus."

**Trip information** — title in black on the left; three text tabs on the right: Details, Itinerary, Dispatch notes.
- *Details:*
  - "Group name: 9th Grade Biology".
  - Two boxes side by side with small grey titles above them (outside the box): **Pickup** (`Mon 11/09 · 07:15`, then the full pickup line) and **Destination** (`Return Mon 11/09 · 14:15`, then the full destination line).
  - **Info** box, full width: the contract's info text.
  - Three boxes in a row: **Passengers**, **Group contact** (name, phone under it), **Driver request** (driver name or "None").
  - All boxes: light grey fill `#F7F8FA`, thin border, 4px radius.
- *Itinerary:* one grey box with the itinerary text, line breaks preserved. Empty shows an empty box (no dash).
- *Dispatch notes:* a labeled textarea, placeholder "Add notes for dispatch", and "Notes save automatically as you type."

**Assign driver & bus**
- **Driver** select: "Select driver…" then all active drivers; the requested driver is labeled `Luis Ortega (requested)`. When a driver is chosen, "Phone: (201) 555-0102" shows under it.
- **Bus** select: "Select bus…" then `#4512 · 56-pax MCI J4500`. A capacity or lift warning shows under it as a small orange note (rule R18).
- **Report time** select: "Select time…" then every 15 minutes from 00:00 to 23:45.
- **Assign** (primary blue) and **Reset** buttons; a small "Assigned" confirmation appears after saving.
- **Booking terminal** section below a divider: two read-only boxes, **Terminal** (`NJ`) and **Total buses** (`2`).

## Booking tab

See `design/screenshots/02-booking-contract-view.png` and `03-booking-contract-form.png`. Both screenshots show only the top of the contract; the sections further down are listed below. Two stacked surfaces of the same width: the contract list, then the contract.

### Contract list surface
1. **Toolbar:** the same ‹ Start/End date › Today controls as the board (same shared range), separator, **All contracts ▾** filter (All contracts, Active contracts, Booked, Quotes, Cancelled), separator, then a 300px search box, placeholder "Search contract, org, group, contact…". (Search and Contract lookup swapped places from the prototype: search filters the list right above it, lookup jumps to one contract.)
2. **Table** (max height about 260px, scrolls): Contract # (monospace, black) · Status · Begin (`11/09/2026 07:15`) · Organization · Group · Route (`Union City → Jersey City`) · Buses · Total · Balance · Payment. Money columns are right-aligned.
   - Status is plain colored text, not a badge: **Booked** blue `#1F5FBF`, **Quote** amber `#8F5A06`, **Cancelled** red `#C0261B`.
   - Payment text: Paid in full green `#1B5530`, Deposit paid / Partially paid amber, Unpaid red, all semi-bold.
   - Cancelled rows are greyed and struck through (except the status word).
   - Click a row to open the contract below; the open row has the dark 2px outline.
   - Empty state: "No contracts match these dates, filter or search."
3. **Status bar under the table:** **12** contracts · **10** booked · **1** quotes · **1** cancelled · **$18,600.00** balance due (cancelled and balance numbers in red).

### Contract surface — view mode
Header row: on the left the **Contract lookup** label with a 130px input (placeholder "e.g. 24817"); "No contract 99999 found." appears beside it in orange when there is no match. Buttons on the right: **+ Insert contract** (secondary), **Edit contract** (primary), **Delete contract** (three-click, rule R10), **Open on board** (switches tab and selects the contract's first unit). A thin line under the header row, then the title "Contract **24817**" (number in monospace bold) with the status as small grey text beside it (red when cancelled), directly above the Job section.

Below, read-only sections. Each section has a small blue title, and each field is a small grey label above a light grey read-only box. Five fields per row.

| Section | Fields |
|---|---|
| Job | Contract #, Organization, Group name, Passengers, Contract status |
| Group contact | Contact name, Phone |
| Schedule | Begin date, Spot time, Start time, Return date, Return time |
| Locations | **Pickup:** Location (full width), Address (full width), then State, City, ZIP code, County. **Destination:** the same. |
| Itinerary | One box, line breaks preserved |
| Vehicle & driver | Number of buses, Terminal, Size requirement, Requested driver, then Info (full width) |
| Pricing | Total price, Deposit required, Total paid (incl. deposit), Balance due, Payment status |
| Dispatch | Single-bus contracts: Driver, Driver phone, Report time, Actual report, Bus, Confirmation. Multi-bus: a one-line note "This contract has 2 buses (24823-1 to 24823-2 on the dispatch board). Driver, bus and report details are set per bus there." |
| Dispatch notes | One box under the section title (no dash when empty) |

A contract is always open. On first visit it is the first contract in the list (or, if the dates and filter show none, the lowest-numbered contract in the sandbox). Deleting the open contract opens the next contract by number, or the previous one if it was the highest. Only when the sandbox has no contracts at all: "Pick a contract from the list, or look one up, to see it here." and an Insert contract button.

### Contract surface — form mode (Insert / Edit)
Title "Insert contract" or "Edit contract 24817". Same sections and order as view mode, minus Dispatch and Dispatch notes, with inputs instead of boxes. Required fields have a red asterisk after the label.

- **Job:** Contract # is read-only (next number for inserts). Contract status is a select (Booked, Quote, Cancelled), default Booked.
- **Schedule:** Begin date and Return date are date inputs. Spot, Start and Return time are **time comboboxes**: a text input with a dropdown arrow listing every 15 minutes `00:00`–`23:45`. Typing digits filters the list by prefix and highlights the first match (`7` → `07:00`…, `73` → `07:30`); Enter picks the highlight; the list scrolls to the current value when opened; leaving the field normalizes what was typed (rule R02). The Return time list starts with **One way**.
- **Locations:** Location (optional, placeholder "e.g. school, hotel, stadium") and Address (required) on their own full-width rows, above State (select), City (select filtered by state), ZIP code, County (read-only box filled from the ZIP).
- **Itinerary:** textarea, placeholder "Enter itinerary".
- **Vehicle & driver:** Number of buses (number), Terminal (select), Size requirement (select of 8 options), Requested driver (select, "No request" first), Info (textarea).
- **Pricing:** Total price, Deposit required, Total paid (incl. deposit) as text inputs with placeholder `$0.00`; Balance due and Payment status are read-only and update live.
- **Buttons:** **Add contract** / **Save changes** (primary) and **Cancel**. There is no "Clear form" button.
- Validation errors appear as a list above the buttons, using the exact messages from the prototype's `validateForm` function.

## Accessibility and interaction details to keep
- Every control is reachable and usable by keyboard; popovers close on Escape and on outside click.
- Sort buttons, resize handles and drag handles have `aria-label`s (see prototype).
- Toggle buttons use `aria-pressed`. The status bar uses `role="status"`.
- Focus ring: 2px `#2F6BC0`.
