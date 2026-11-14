# CharterStack — Product Spec

CharterStack is a small transportation management system (TMS) for a motorcoach charter company. It has two screens that share one set of data:

- **Booking** — sales creates and edits charter contracts (who, when, where, how many buses, price).
- **Dispatch board** — dispatch works each day's trips: assigns a driver and bus, sets report times, stamps actual report and on-location times, confirms, cancels.

It is a portfolio project. The goal is a deployed full-stack app that looks and behaves like a real internal operations tool, built by someone who has worked dispatch.

## Who uses it

One kind of user: a **demo visitor**. They click "Try the demo", get a private copy of the sample data, and can use both screens freely. There is no sign-up, no password, and no roles in v1.

## Tech stack (decided)

| Layer | Choice |
|---|---|
| Backend | Python 3.12+, Django 5, Django REST Framework |
| Database | PostgreSQL (SQLite is fine for local development) |
| API docs | drf-spectacular (Swagger UI at `/api/docs/`) |
| Frontend | React 18+ with Vite and TypeScript |
| Data fetching | TanStack Query |
| Tests | pytest + pytest-django (backend), Vitest + React Testing Library (frontend) |
| CI | GitHub Actions: lint + tests on every push |
| Hosting | One fixed-price instance (Render or Railway), autoscaling off. Django serves the built React app. |

## Scope for v1

In scope:

1. Demo login with a private, auto-expiring sandbox per visitor. See `DEMO_SANDBOX.md`.
2. Booking: contract list with date range, status filter, search and lookup; insert, view, edit and delete contracts; pricing; contract status (Booked, Quote, Cancelled).
3. Dispatch board: trip table with date range, terminal filter, trip view filter, search, sorting, resizable and draggable columns; trip information panel; assign driver, bus and report time; Reported, On location and Cancelled actions; confirmation initials; dispatch notes; duplicates; multi-bus contracts; Excel export.
4. Bus board: one terminal's fleet at a time (terminal buttons), one row per bus model in increasing bus-number order, each bus showing its trips in the shared date range or Available.
5. Session strip at the bottom of the page.
6. Django admin for reference data (drivers, buses, terminals), protected by a real superuser password.
7. Documentation: README, API docs, data model diagram, docstrings on business rules.

Out of scope for v1 (do not build unless asked):

- Real user accounts, sign-up, password reset, roles.
- Driver hours-of-service checks.
- Hard-blocking double-booking of drivers or buses (see "Optional later" below).
- Payments processing, invoices, emails, customer confirmations.
- Mobile layouts. The app targets a desktop browser at 1280px wide and up.
- Real-time updates between browsers.

Optional later (version 2 ideas, listed so the design leaves room):

- API rule that refuses to assign a driver or bus already on an overlapping trip.
- Trip completion (actual return time) and a per-trip change history.
- Saved customers that pre-fill the contact fields.

## The documents in this pack

| File | What it covers |
|---|---|
| `CLAUDE.md` | Project conventions for Claude Code. Read first every session. |
| `docs/SPEC.md` | This file: what the product is and what v1 includes. |
| `docs/UI_GUIDE.md` | Exactly how each screen looks and behaves. |
| `docs/DATA_MODEL.md` | Django models, fields and relationships. |
| `docs/BUSINESS_RULES.md` | Every rule the backend must enforce or compute. |
| `docs/API.md` | REST endpoints, request and response shapes. |
| `docs/DEMO_SANDBOX.md` | Demo login, per-visitor data isolation, cleanup, safeguards. |
| `docs/BUILD_PLAN.md` | Build order in phases, with "done" checks for each. |
| `design/Main.dc.html` | The interactive design prototype (reference for markup, CSS and logic). |
| `design/screenshots/` | Screenshots of the three main screens. |
| `seed/seed_demo.json` | Sample data: 12 contracts, 10 drivers, 8 buses, 5 terminals, ZIP lookup. |

## Definition of done for v1

- A visitor opens the live URL, clicks "Try the demo", and lands on the dispatch board with sample trips dated today.
- Everything in `UI_GUIDE.md` works against the real API and survives a page reload.
- Two visitors in different browsers never see each other's changes.
- `pytest` passes, including tests for every rule in `BUSINESS_RULES.md` and for sandbox isolation.
- CI is green on the main branch.
- `/api/docs/` shows every endpoint.
- The README explains the project, shows screenshots, links the live demo, and explains how to run it locally.
