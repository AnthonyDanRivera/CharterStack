# Demo Login and Sandbox

There are no real accounts. A visitor clicks one button and gets a private, temporary copy of the sample data. Nothing one visitor does is ever visible to another.

## Flow

1. The visitor opens the site. React calls `GET /api/session/`. With no session, it shows the **landing page**: the CharterStack logo, the headline "Booking and dispatch for a charter bus company.", two plain sentences on what it does, the primary button **Try the demo**, and a small line under it: "No sign-up. You get a private copy of the sample data that resets after 24 hours." Below: a screenshot of the board, a "How it's built" section (API, frontend, database, tests, deployment), and a footer: "Built by Anthony Rivera, a former charter dispatcher." with a link to anthonydanrivera.com (new tab). The builder is mentioned once, in the footer.
2. The button calls `POST /api/demo-login/`. The server:
   1. Creates a Django `User` with a random username such as `demo_8f3k2` and an unusable password.
   2. Creates a `DemoSession` row: `user`, `short_id` (`DEMO-8F3K2`), `created_at`, `ip_hash`.
   3. Copies the sample contracts and trip units from `seed/seed_demo.json` into the database with `owner = user` (see "Seeding").
   4. Logs the user in with Django's session auth.
3. React loads the dispatch board. The session strip shows `User Demo User` and `Session DEMO-8F3K2`.
4. Returning within 24 hours in the same browser resumes the same sandbox (the session cookie is still valid).

## Isolation rule (the important part)

Every visitor-owned model (`Contract`, `TripUnit`) has an `owner` foreign key. **No query may read or write those models without filtering by `request.user`.**

Implement it once, not per view:

- A base class `OwnedModelViewSet` (or mixin) whose `get_queryset()` returns `Model.objects.filter(owner=self.request.user)` and whose `perform_create()` sets `owner=self.request.user`. Every viewset for owned models inherits from it.
- Lookups of related objects (for example the contract of a unit) go through the same filtered querysets.
- An object owned by someone else returns **404**, not 403.

Required tests (`tests/test_isolation.py`):
- User A's list endpoints never include user B's rows.
- User A gets 404 on GET, PATCH, DELETE and every action endpoint for user B's contract and unit IDs.
- User A cannot create a unit or duplicate attached to user B's contract.
- Contract numbers are independent per owner (both sandboxes can have 24817).

## Seeding

`seed/seed_demo.json` holds reference data and 12 sample contracts dated around a base day of **2026-11-09**.

- `python manage.py seed_reference` — loads terminals, drivers, buses and ZIP codes. Idempotent. Run on deploy.
- `seed_sandbox(user)` — a service function called by demo login. It copies the 12 contracts and creates their units, **shifting every date so the base day becomes today** in the visitor's time zone. The board must open with trips on today's date.
  - Dispatch data in the seed (driver, bus, report time, confirmation) goes on unit 1 of each contract. Confirmation timestamps shift by the same number of days.
  - Contract 24823 has `bus_count: 2`: unit 1 gets the seeded driver, unit 2 starts blank.
  - In `unit1`, `driver` is a driver name and `bus` is a bus number; look them up in the reference tables.
  - Contract 24841 is a quote; 24844 is cancelled.
- Seeding one sandbox is about 12 contracts and 13 units. Use `bulk_create`.

## Cleanup

`python manage.py cleanup_demo` deletes demo users whose `DemoSession.created_at` is older than 24 hours. Their contracts and units go with them through `on_delete=CASCADE`. Schedule it once a day (Render cron job or equivalent). It must never touch superusers or reference data: select strictly by `username__startswith="demo_"` **and** an existing `DemoSession`.

## Safeguards (keep it simple)

| Risk | Safeguard |
|---|---|
| Surprise hosting bill | Fixed-price instance, autoscaling off. Overload means slow, not expensive. |
| Request spam | DRF throttling: `anon` 30/min, `user` 120/min. |
| Sandbox spam | `demo-login` has its own throttle scope: 5 per hour per IP. |
| Data bloat inside one sandbox | Max 200 contracts per owner; creating more returns 400 "Demo limit reached." Max 20 duplicates per contract. |
| Huge text | Field `max_length`s from `DATA_MODEL.md`; itinerary, info and notes capped at 2,000 characters. |
| Admin exposure | `/admin/` requires a real superuser created from environment variables at deploy. Demo users have `is_staff = False`. |

No profanity filter is needed: nobody can see anyone else's text.

## Things that are deliberately not here
- Sign-up, passwords, email, password reset.
- Roles or permissions beyond "logged-in demo user".
- A shared dataset or a nightly reset.
