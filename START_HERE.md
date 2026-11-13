# Start here

This folder is everything Claude Code needs to build CharterStack as a full-stack app.

## 1. Set up the repo

1. Create an empty folder named `charterstack` and copy everything from this pack into it, keeping the folder structure.
2. Open a terminal in that folder and run `git init`.
3. Start Claude Code in that folder.

## 2. First message to Claude Code

Paste this:

```
Read CLAUDE.md, then docs/SPEC.md, docs/BUILD_PLAN.md and docs/DATA_MODEL.md.
Look at the three screenshots in design/screenshots/.

Then do Phase 0 from docs/BUILD_PLAN.md only. Before you write code, tell me:
1. what you will set up,
2. anything in the docs that is unclear or contradictory,
3. what I need installed on my machine.

Stop when Phase 0's checks pass and summarize what you did.
```

## 3. For each later phase

```
Start Phase N from docs/BUILD_PLAN.md. Read the docs that phase depends on first
(for backend phases: BUSINESS_RULES.md, API.md, DEMO_SANDBOX.md; for frontend
phases: UI_GUIDE.md and design/Main.dc.html). List what you will build and any
questions, then build it with tests. Stop when the phase's checks pass and
summarize what you built, what you tested, and any decisions the docs did not cover.
```

## 4. Tips

- **One phase per session.** Start a fresh Claude Code session for each phase so it stays focused; `CLAUDE.md` gives it the context every time.
- **Commit after every phase.** If a phase goes wrong you can go back.
- **For the UI phases**, ask it to open the app in a browser and compare against the screenshots before calling a phase done.
- **When you change your mind about a rule**, change the doc first, then ask Claude Code to update the code and tests to match. The docs stay the source of truth.
- **Ask it to explain.** You will be asked about this code in interviews. After each phase, ask "walk me through how X works" for the parts you want to be able to explain: sandbox isolation, payment status, the unit model.

## What is in this pack

```
START_HERE.md            this file
CLAUDE.md                project rules Claude Code reads every session
README.md                starter README for GitHub (finish after deploy)
docs/
  SPEC.md                what the product is, scope, definition of done
  UI_GUIDE.md            how every screen looks and behaves
  DATA_MODEL.md          Django models
  BUSINESS_RULES.md      33 numbered rules, each needs a test
  API.md                 endpoints and JSON shapes
  DEMO_SANDBOX.md        demo login, per-visitor data, cleanup, safeguards
  BUILD_PLAN.md          phases 0 to 8, each with checks
design/
  Main.dc.html           the interactive prototype (reference)
  screenshots/           dispatch board, contract view, contract form
seed/
  seed_demo.json         12 contracts, 10 drivers, 8 buses, 5 terminals, ZIP lookup
```
