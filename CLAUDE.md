# CharterStack — instructions for Claude Code

CharterStack is a charter-bus dispatch board and booking app: a portfolio project built with Django REST Framework and React. Read `docs/SPEC.md` first, then the doc for whatever you are working on.

## Where things are
- `docs/SPEC.md` — scope and definition of done.
- `docs/BUILD_PLAN.md` — phases. Work on one phase at a time, in order.
- `docs/DATA_MODEL.md`, `docs/BUSINESS_RULES.md`, `docs/API.md`, `docs/DEMO_SANDBOX.md` — backend.
- `docs/UI_GUIDE.md`, `design/` — frontend look and behavior. `design/Main.dc.html` is a prototype to read, not code to copy.
- `seed/seed_demo.json` — sample data.

## Stack
Django 5 + Django REST Framework + PostgreSQL (SQLite locally) · drf-spectacular · pytest-django · React + Vite + TypeScript · TanStack Query · Vitest · GitHub Actions.

## Commands
Backend (from `backend/`, Python 3.12 managed by uv — prefix commands with `uv run`):
- `uv sync` — install dependencies into `.venv`
- `uv run python manage.py runserver` — API on :8000
- `uv run python manage.py migrate && uv run python manage.py seed_reference` — schema plus reference data (idempotent)
- `uv run python manage.py cleanup_demo` — delete demo sandboxes older than 24 hours
- `uv run pytest` — all backend tests
- `uv run ruff check . && uv run ruff format --check .`
- `uv add <pkg>` / `uv add --dev <pkg>` — add a dependency (updates `pyproject.toml` and `uv.lock`)

Frontend (from `frontend/`):
- `npm run dev` — app on :5173, proxies `/api` to :8000
- `npm test` · `npm run lint` (ESLint + Prettier check) · `npm run format` · `npm run build`
- Windows: if Vitest says "failed to find the current suite", the shell's drive letter is lowercase (`c:\...`). Run it from `C:\...` (e.g. PowerShell `Set-Location C:\Users\...\frontend`). CI is unaffected.

CI: `.github/workflows/ci.yml` runs backend lint + tests (against PostgreSQL) and frontend lint + tests + build on every push.

Keep this section accurate when commands change.

## Rules that must not be broken
1. **Sandbox isolation.** Every query on `Contract` or `TripUnit` filters by `owner=request.user`. Use `OwnedModelViewSet` (set `model`, not `queryset`) and `OwnedPrimaryKeyRelatedField` from `charters/api/ownership.py`. Add every new owned endpoint to `charters/tests/test_isolation.py`. Never write `Contract.objects.all()` or `.get(pk=...)` in a view. Another owner's object returns 404.
2. **Business rules live in Django.** Payment status, balance, effective status, display numbers, warnings, counts, day labels and time normalization are computed in the backend and tested with pytest. React displays what the API returns.
3. **Every rule in `docs/BUSINESS_RULES.md` has a test** named with its ID, for example `test_r12_payment_status_deposit_paid`.
4. **24-hour times everywhere.** `HH:MM`. No AM/PM in UI, API or exports.
5. **No real auth features.** No sign-up, passwords, or roles. Demo login only.
6. **Match the design.** Colors, sizes, labels and wording come from `docs/UI_GUIDE.md` and the prototype's final CSS. Plain text, no badges or pills, no emoji, no new visual ideas unless asked.

## Conventions
- Python: ruff defaults, type hints on service functions, docstrings on anything implementing a business rule (mention the rule ID).
- Put multi-step logic in `charters/services.py` (booking, sandbox) or `charters/board.py` (dispatch board, unit actions, export); keep views and serializers thin. Money parsing/formatting is in `charters/money.py`; per-row computed values (balance, payment status, display number) are model properties in `charters/models.py`.
- API field names are `snake_case`. Frontend types mirror the API shapes in `docs/API.md`.
- React: function components, one component per file, colocated CSS modules or a single `tokens.css` + component CSS. No UI library; the look is custom and small.
- Server state through TanStack Query; UI state (open popovers, column order, widths) in component state, with column order and widths persisted to localStorage.
- User-facing text uses the exact strings from the UI guide.
- Commits: small, present tense, one concern each ("Add contract lookup endpoint").

## How to work with me (the owner)
- I come from bus dispatch operations and I am building this to show full-stack skills. Explain non-obvious technical choices briefly as you make them.
- Before starting a phase, list what you will build and ask about anything unclear. After finishing, summarize what was built, what was tested, and anything you chose that the docs did not specify.
- If the docs and the prototype disagree, follow the docs and tell me.
- Do not add features that are listed as out of scope in `docs/SPEC.md`.
- Update `README.md` and this file when setup steps, commands or structure change.
