# Build Plan

Build in this order. Each phase ends with something that runs and a short list of checks. Do not start a phase until the previous phase's checks pass. Commit at the end of each phase. Update `README.md` and the API docs as part of each phase, not at the end.

## Phase 0 — Project setup
- Repo layout:
  ```
  charterstack/
    backend/        Django project `config`, app `charters`
    frontend/       Vite + React + TypeScript
    docs/           this documentation
    design/         prototype and screenshots
    seed/           seed_demo.json
    CLAUDE.md  README.md
  ```
- Backend: Django, DRF, drf-spectacular, pytest-django, ruff. Settings read from environment variables (`DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`).
- Frontend: Vite, React, TypeScript, TanStack Query, Vitest, ESLint, Prettier. Dev proxy `/api` → Django.
- GitHub Actions workflow: backend lint + tests, frontend lint + tests + build.

**Checks:** `pytest` runs (even with one trivial test); `npm run build` succeeds; CI is green; `GET /api/health/` returns ok.

## Phase 1 — Data model and reference data
- Models from `DATA_MODEL.md`, migrations, Django admin registration for all models.
- `seed_reference` command.
- Model-level computed values: `balance_due`, `payment_status`, `needs_wc`, unit `display_number`.

**Checks:** tests for rules R11–R13, R15; admin lists drivers, buses, terminals after seeding.

## Phase 2 — Demo login and sandbox
- `DemoSession` model, `POST /api/demo-login/`, `GET /api/session/`, logout.
- `seed_sandbox(user)` with date shifting.
- `OwnedModelViewSet` base class.
- `cleanup_demo` command. Throttles.

**Checks:** isolation tests from `DEMO_SANDBOX.md` pass; a new sandbox has 12 contracts and 13 units with the base day equal to today; cleanup deletes only expired demo users.

## Phase 3 — Booking API
- Contract list (filters, search, summary), detail, create, update, delete, next-number, lookup, ZIP lookup, reference endpoint.
- Time normalization (R02), validation (R03–R05, R08, R13), unit sync on bus count change (R14).

**Checks:** tests for R02–R10, R14, R31–R33; Swagger shows the endpoints.

## Phase 4 — Board API
- `GET /api/board/` with range, view, terminals, search, counts, day labels.
- Unit detail and PATCH (assign, initials, notes) with warnings.
- Actions: reported, on-location, cancel, duplicate, delete duplicate.
- Excel export.

**Checks:** tests for R07, R16–R30; an exported file opens with openpyxl in a test and has the right header and row count.

## Phase 5 — Frontend shell
- Landing page with "Try the demo".
- App frame: header, tabs, session strip (live clock, session time).
- Shared date-range state, calendar popover, outside-click closing.
- API client with CSRF handling; TanStack Query setup; error and loading states.
- Global CSS ported from the prototype's final rules, as CSS variables for the tokens in `UI_GUIDE.md`.

**Checks:** clicking the button creates a session and shows an empty app frame; reloading keeps the session; the clock ticks.

## Phase 6 — Dispatch board UI
In this order: static table with real data → toolbar filters and status bar → row selection and trip information panel → assign panel → action bar buttons → initials and notes editing → sorting → column resize → column drag → reset columns and localStorage → Excel export button.

**Checks:** side-by-side with `design/screenshots/01-dispatch-board.png` it matches; every board item in `UI_GUIDE.md` works; component tests for the time combobox and terminal filter.

## Phase 7 — Booking UI
Contract list and toolbar → status bar and search → contract view → insert/edit form with time comboboxes, ZIP auto-fill, live pricing → delete with three clicks → "Open on board".

**Checks:** matches screenshots 02 and 03; creating a booked contract makes it appear on the board for its date; a quote does not; cancelling turns its board rows red.

## Phase 8 — Polish, docs, deploy
- Empty, loading and error states everywhere ("Couldn't load trips. Retry").
- README final pass with screenshots, Mermaid model diagram, live link.
- Docstrings on every business-rule function, referencing rule IDs.
- Deploy: one web service (Django + built React via WhiteNoise), PostgreSQL, daily cron for `cleanup_demo`, superuser from env vars.
- Smoke test on the live URL in two browsers at once.

**Checks:** everything in "Definition of done" in `SPEC.md`.

## Working agreements for each phase
- Write the tests for a rule with (or before) the code for it.
- Keep business rules out of React. If the frontend needs a derived value, add it to the API.
- When the prototype and these docs disagree, the docs win; say so in the commit message.
- When something is unclear, ask before building.
