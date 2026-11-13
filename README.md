# CharterStack

A dispatch board and booking system for a motorcoach charter company, built with Django REST Framework and React.

**Live demo:** _add link after deploy_ — click **Try the demo**. No sign-up; you get a private copy of the sample data.

![Dispatch board](design/screenshots/01-dispatch-board.png)

## Why I built this

I worked as a dispatcher and operations planner in the motorcoach charter business. Every day ran on a dispatch board: which trips go out, who is driving, which bus, when the driver reports, whether the trip is confirmed. CharterStack is my version of that tool, built to show how I turn real operations into software.

## What it does

**Booking** — sales creates charter contracts.
- Insert, edit, view and delete contracts: group, contact, schedule, pickup and destination, itinerary, vehicles, pricing.
- Contract status: Quote, Booked, Cancelled. Balance due and payment status are computed.
- Contract list by date range, with status filter, search and lookup.

**Dispatch board** — dispatch works the day's trips.
- One row per bus. A two-bus contract shows as `24823-1` and `24823-2`.
- Assign driver, bus and report time, with warnings when the bus is too small or has no wheelchair lift.
- Stamp Reported and On location times, cancel, add confirmation initials and dispatch notes.
- Filter by date range, terminal, and today / away / all trips. Search, sort, resize and reorder columns.
- Export the current view to Excel.

Quotes never reach the board; cancelled contracts stay visible in red.

## How the demo works

Clicking **Try the demo** creates a temporary user and copies the sample data for that user only. Every database query is scoped to the logged-in user, so visitors never see each other's changes. Sandboxes are deleted after 24 hours. Details: [docs/DEMO_SANDBOX.md](docs/DEMO_SANDBOX.md).

## Tech stack

| | |
|---|---|
| Backend | Python, Django, Django REST Framework, PostgreSQL |
| Frontend | React, TypeScript, Vite, TanStack Query |
| Testing | pytest, Vitest, GitHub Actions |
| API docs | OpenAPI / Swagger at `/api/docs/` |

## Data model

```mermaid
erDiagram
    User ||--o{ Contract : owns
    Contract ||--|{ TripUnit : "has 1..n"
    Terminal ||--o{ Contract : "booked at"
    Driver ||--o{ TripUnit : "assigned to"
    Bus ||--o{ TripUnit : "assigned to"
```

A **Contract** is what sales books. A **TripUnit** is one bus on that contract and one row on the dispatch board. Full details: [docs/DATA_MODEL.md](docs/DATA_MODEL.md).

## Run it locally

Requirements: [uv](https://docs.astral.sh/uv/) (installs Python 3.12 for you) and Node.js 22 or newer.

```bash
# backend (first terminal)
cd backend
uv sync                                  # creates .venv with Python 3.12 + dependencies
uv run python manage.py migrate
uv run python manage.py seed_reference   # terminals, drivers, buses, ZIP codes (safe to re-run)
uv run python manage.py createsuperuser  # optional: to browse reference data at /admin/
uv run python manage.py runserver        # API on http://localhost:8000

# frontend (second terminal)
cd frontend
npm install
npm run dev                              # app on http://localhost:5173, proxies /api to :8000
```

Open http://localhost:5173. Health check: http://localhost:8000/api/health/. API docs: http://localhost:8000/api/docs/.

Local development uses SQLite with no setup. To use PostgreSQL, set `DATABASE_URL` (see [backend/.env.example](backend/.env.example)).

## Tests

```bash
cd backend && uv run pytest
cd backend && uv run ruff check . && uv run ruff format --check .
cd frontend && npm test && npm run lint && npm run build
```

GitHub Actions runs all of these on every push, with the backend tests against PostgreSQL.

Every business rule in [docs/BUSINESS_RULES.md](docs/BUSINESS_RULES.md) has a named test, and sandbox isolation has its own test suite.

## Documentation

- [Product spec](docs/SPEC.md)
- [UI guide](docs/UI_GUIDE.md)
- [Data model](docs/DATA_MODEL.md)
- [Business rules](docs/BUSINESS_RULES.md)
- [API](docs/API.md)
- [Demo sandbox](docs/DEMO_SANDBOX.md)
- [Build plan](docs/BUILD_PLAN.md)

## Screenshots

| Booking: contract view | Booking: contract form |
|---|---|
| ![Contract view](design/screenshots/02-booking-contract-view.png) | ![Contract form](design/screenshots/03-booking-contract-form.png) |

## Author

Anthony Rivera — _add portfolio and LinkedIn links_
