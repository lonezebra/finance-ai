# CLAUDE.md — Open CFO

This file is the canonical steering doc for any AI assistant (Claude Code or otherwise)
working on this repository. Read it before making changes. It is a distilled version of
`OPEN_CFO_PROJECT_HANDOFF.md`, which remains the full source of truth for deep detail —
consult it when this file doesn't cover something.

> **Know what changed. Know what matters. Know what to do next.**

---

## 0. Non-Negotiable Rules

1. **Architecture is frozen.** Do not propose broad redesigns unless a genuine blocker is found.
2. **Local-first, always.** Financial data stays on the user's machine. No cloud API key required.
3. **Python calculates. AI reasons.** The LLM never performs financial math (net worth, cash flow,
   savings rate, DTI, emergency fund, scores, decisions) — it only explains, discusses, and narrates.
4. **AI never silently changes data.** Any AI-driven data mutation must: propose → show the diff →
   confirm → execute via validated Python tools → audit-log → backup if appropriate.
5. **SQLite is the source of truth.** Dashboards, reports, and AI context all read from it.
6. **Do not restart or rename the project.**
7. **Never claim a change was made in the user's actual repo unless the user confirms it** — this
   project's private GitHub repo is authoritative, and this environment may only hold a
   reconstruction.
8. **Error handling, security, observability, and scalability are standing requirements, not a
   later retrofit.** Weigh all four for every new feature, function, or scope as it's being built —
   proportionate to what this app actually is (local-first, single-user desktop app, not a
   multi-tenant service). Don't stop current work to do a giant hardening pass, but don't build new
   surface area that ignores them either. See §8's Cross-Cutting Concerns Checklist for the current
   gap list — update it as gaps are found or closed.

---

## 1. Product Identity

- **Product name:** Open CFO
- **Repository:** `finance-ai` (private)
- **Python package:** `finance_ai`

**Mission:** a local-first personal CFO that helps individuals and families understand their
financial position, keep clean records, find the highest-impact next action, evaluate tradeoffs,
run what-if scenarios, and discuss it all with a private local AI advisor.

**North star:** *Open CFO consistently identifies the highest-impact next financial action, backs
it with transparent calculations and trusted data, and lets the user stress-test that action
through scenario planning.*

The product must be exceptional at two things: **Next Best Action** and **Scenario Planning**.

Every major feature should answer one of: What changed? What is risky? What should I do next?
What happens under a different path? How confident is Open CFO in the answer?

---

## 2. Architecture (Frozen)

```text
Excel / CSV / Manual Entry
           |
           v
      Import Engine
           |
           v
     SQLite Database
           |
           v
      Finance Engine
           |
           +--------------------+
           |                    |
           v                    v
     Timeline Engine       Decision Engine
           |                    |
           +----------+---------+
                      |
                      v
             Executive Report Engine
                      |
                      v
                Strategic Advisor
                      |
                      v
                  AI Runtime
                      |
                      v
              LM Studio Provider
                      |
                      v
             Local LLM (swappable)
```

The desktop UI is a presentation adapter over these systems.

| Layer | Responsibility |
|---|---|
| Excel/CSV | Human-friendly data entry and import formats |
| SQLite | Application source of truth |
| Finance Engine | Deterministic calculations (net worth, cash flow, savings rate, DTI, emergency fund) |
| Timeline Engine | Point-in-time snapshots and comparisons |
| Decision Engine | Deterministic, explainable, ranked candidate decisions |
| Executive Report Engine | Combines snapshot + changes + strengths/concerns + top decisions |
| Strategic Advisor | Finance-specific AI-facing service; prepares context for the AI Runtime |
| AI Runtime | Model-agnostic execution layer; loads prompts, calls provider, returns text |
| Local model | Reasons, explains, discusses tradeoffs — never owns the math |

---

## 3. Repository Structure

```text
finance-ai/
├── Makefile, pyproject.toml, uv.lock, README.md, ROADMAP.md, CHANGELOG.md
├── alembic.ini, alembic/           # DB schema migrations -- see §8 known issue #2
│   ├── env.py, script.py.mako, versions/
├── assets/
│   ├── prompts/            # executive_briefing.md, strategic_advisor.md, scenario.md
│   │                       # (implemented), financial_qa.md, goal_planning.md,
│   │                       # explain_decision.md (placeholders)
│   ├── icons/, themes/
├── docs/
│   ├── PRODUCT_SPEC.md, DOMAIN_MODEL.md, DATA_MODEL.md, ENGINEERING.md,
│   │   AI_ARCHITECTURE.md, COMMANDS.md, DEVELOPMENT_SETUP.md,
│   │   RELEASE_CHECKLIST.md, DECISIONS.md, decisions/
├── data/
│   ├── finance.db (gitignored), imports/, exports/finance_template.xlsx
├── backups/ (gitignored contents), logs/, reports/
├── tests/
│   ├── test_opportunities.py, test_timeline.py, test_decision_engine.py, test_formatter.py,
│   │   test_scenario_engine.py, test_scenario_formatter.py, test_background.py,
│   │   test_thinking.py, test_errors.py, test_briefing_presenter.py,
│   │   test_import_presenter.py, test_import_errors.py
└── src/finance_ai/
    ├── config.py
    ├── ai/          # runtime, advisor, thinking state, prompt loading
    ├── core/
    ├── db/          # SQLAlchemy models, init_db
    ├── decision/    # Decision Engine
    ├── exports/
    ├── finance/     # Finance Engine, Opportunity Engine (legacy)
    ├── history/     # Timeline Engine (snapshots, comparison, interpretation)
    ├── imports/     # reader, validator, mapper, importer, errors
    ├── reports/     # Executive Report Engine + formatter.py
    ├── scenario/    # Scenario Engine (models, engine, formatter)
    └── ui/          # CustomTkinter desktop shell (report_cards.py, import_view.py, presenters/)
```

**Note:** this environment's project knowledge also contains a `reconstructed_project/` tree — a
best-effort recovery scaffold, not guaranteed to match the real repo byte-for-byte. Compare before
patching existing core files; ask the user for the current file content when in doubt.

---

## 4. Data Model (SQLite / SQLAlchemy)

| Table | Key fields |
|---|---|
| `accounts` | name, account_type, institution, current_balance, notes |
| `categories` | name (unique), category_type (income/expense/transfer) |
| `transactions` | transaction_date, merchant, description, amount, account_id, category_id, notes — **positive = inflow, negative = expense** |
| `debts` | name, lender, balance, interest_rate, minimum_payment, due_day, notes |
| `assets` | name, asset_type, current_value, notes |
| `budgets` | month (`YYYY-MM`), category_name, budgeted_amount |
| `goals` | name, target_amount, current_amount, target_date, notes |
| `ai_notes` | created_at, note_type, content |
| `import_batches` | imported_at, source_file, source_type, status, notes |
| `audit_log` | created_at, action, details |
| `financial_snapshot_records` | month + all snapshot metrics (see below) |

### Excel import contract
Required sheets: Accounts, Categories, Transactions, Debts, Assets, Budgets, Goals (exact required
columns per sheet are in the full handoff, §8). Validation rule IDs: `V001` missing sheet, `V002`
missing column, `V003` missing required value, `V004` invalid number, `V005` invalid date.

Pipeline: `read_excel_workbook() → WorkbookData → validate_workbook() → ValidationReport →
map_workbook() → ImportDataset → import_dataset()`. Runs in one atomic SQLAlchemy transaction.
**Done — imports are now idempotent** (see Known Issues #1 and `import_dataset()`'s docstring):
accounts, categories, debts, assets, budgets, and goals are upserted by their natural key (name,
or month+category for budgets); re-importing refreshes existing rows instead of duplicating them.
Transactions have no natural key -- they're matched on an exact full-row fingerprint and skipped
if that exact row already exists, so anything even slightly different (e.g. an edited note)
still imports as a new transaction. `import_dataset()` returns a typed `ImportResult`
(created/updated/skipped_duplicate per entity), not a flat counts dict.

---

## 5. Core Domain Objects & Rules

### FinancialSnapshot
`month, total_assets, total_debt, net_worth, cash_balance, monthly_income, monthly_expenses,
monthly_cash_flow, savings_rate, debt_to_income_ratio, emergency_fund_months`

Calculations:
- `total_assets` = sum(account balances) + sum(asset values) — correct **only because the two
  tables are meant to be disjoint** (Accounts = liquid balances, Assets = everything else). See
  the overlap-detection note in §5.
- `net_worth` = total_assets − total_debt
- `monthly_income` = sum of positive transactions in month
- `monthly_expenses` = abs(sum of negative transactions in month)
- `monthly_cash_flow` = income − expenses
- `savings_rate` = cash_flow / income (0 if income is 0)
- `debt_to_income_ratio` = sum(debt minimum payments) / monthly income — **note the basis: this is
  take-home (net) income**, since `monthly_income` is the sum of positive transactions, i.e. money
  that actually landed in an account. Not lender-grade; see the bands note in §5.
- `emergency_fund_months` = cash_balance / monthly_expenses (uses *all* expenses, not essential-only)

### Accounts vs Assets: the disjoint contract (and overlap detection)
**The two tables are defined as mutually exclusive.** Accounts holds liquid balances (the
template's examples are Checking and Savings); Assets holds everything else (Home, Roth IRA).
`total_assets = sum(accounts) + sum(assets)` is only correct under that contract, and
`get_cash_balance()` relies on the same split (it filters accounts to `checking/savings/cash`).
The contract was implicit — the template followed it, the code assumed it, nothing stated or
enforced it.
**Done — violations are now detected and reported, never silently corrected.**
`confidence.py::find_account_asset_overlaps()` finds names present in both tables
(case- and whitespace-insensitive exact match, aggregating duplicates within a table since
account names aren't unique in the schema) and raises a **high-severity Confidence Score
issue** naming the entries and the amount at stake (the *smaller* of the two values — if they
disagree, only the overlapping portion is certainly duplicated). Flat −15 penalty regardless
of overlap count: it's one class of problem, and the message carries the per-entry detail.
**Deliberately does not adjust `total_assets`.** An exact name match is strong evidence but not
proof — a "Vanguard" brokerage account and a "Vanguard" asset row could legitimately be
different things — and silently changing net worth on a guess is worse than the double-count,
because the guess is invisible while the double-count at least shows up as a suspiciously
large number. Matching is exact rather than fuzzy for the same reason: "Savings" vs "Savings
Account" would generate false alarms that train the user to ignore the warning. Widening the
heuristic is a follow-up if exact matching proves too narrow in practice.
*Rejected alternative:* a schema link (`asset.account_id`, or a "already counted" flag). That
creates two sources of truth for one value and immediately raises "which wins when they
disagree?" — significant new ambiguity for little gain over reporting.

### Debt-to-Income bands (`finance/thresholds.py`)
**Done — the income basis was wrong relative to the thresholds.** `monthly_income` is the sum of
positive transactions, i.e. **take-home (net) pay** — the template's own example is a "Paycheck" of
3500 deposited into Checking, and gross pay never lands in a checking account. But the bands being
compared against (25% / 36% / 50%) are the conventional **lender** figures, which are defined on
**gross** income. Applying gross bands to a net denominator reports a systematically inflated
ratio: the same debt burden looks worse purely because the denominator is smaller. Concretely,
someone at ~36% of take-home used to trip "above 36%" → a −10 Health Score penalty, an "elevated"
concern, *and* a shift of `recommended_focus` to "Reduce debt burden" — a false alarm on all three.
Bands are now `DTI_CONSERVATIVE` 30% / `DTI_ELEVATED` 45% / `DTI_HIGH` 60%, the conventional gross
bands scaled for take-home (net is typically ~75–80% of gross with payroll withholding). These are
heuristics like the emergency-fund bands, not lender rules. **Deliberately not** estimating gross
from net via an assumed tax rate — that fabricates a user figure, which Rule 3 rules out; a true
lender DTI would need the user to enter gross income, which the data model doesn't capture.
Centralized in `finance/thresholds.py` because these were previously bare literals duplicated
across `health.py`, `reports/engine.py`, `decision/engine.py` and `opportunities.py` — four copies
that had to move together. User-facing labels now say "(take-home)" so the number isn't silently
compared to the lender benchmark. *Note:* the stored `debt_to_income_ratio` **value** is unchanged,
so `financial_snapshot_records` history stays comparable; only the bands and labels moved.

### Financial Confidence Score
Measures data completeness/trustworthiness, **not** wealth. Starts at 100, subtracts for missing
accounts/transactions/categories/budgets/debts/assets/goals and for uncategorized transactions or
debts missing interest rates. Labels: 90+ High, 70–89 Moderate, 50–69 Low, <50 Very Low.
**Done — data-freshness signal added:** `calculate_financial_confidence_score()` now also checks
how many days old the most recent transaction is (`today` is an injectable parameter, defaulting
to the real current date, so tests aren't tied to when they happen to run) — over
`STALE_AFTER_DAYS` (30) subtracts 10 with a medium-severity issue, over `VERY_STALE_AFTER_DAYS`
(90) subtracts 20 with a high-severity one. Only checked when transactions exist at all (the
existing "no transactions" check already covers the zero case, so the two don't double-penalize
the same underlying problem), and based on the single most recent transaction, not the oldest, so
one fresh import doesn't get dragged down by unrelated old history. This directly fixes the
previously-documented known weakness: the demo data (transactions dated 2026-06) now correctly
scores below 100 when evaluated against a later real-world date, rather than reading as fully
confident despite being stale.
**Done — now surfaced in the UI:** `ExecutiveReport.confidence` (`reports/models.py`) carries a
`FinancialConfidenceScore`, populated by `create_executive_report()` via
`calculate_financial_confidence_score()`. Shown as the first card in the Executive Briefing
(`report_cards.py::build_confidence_card()`, captioned to make the "not wealth" distinction
explicit so it isn't confused with the Health Score) and included in
`format_executive_report_for_ai()`'s output, so the AI narrative and chat can reference data
caveats too. Defaults to a clean 100/High score when not explicitly set (e.g. in tests that
construct an `ExecutiveReport` directly), so a missing value never implies an unassessed problem.

### Financial Health Score
Measures the financial condition itself. Starts at 100, subtracts for no income, negative cash
flow, low savings rate, low emergency fund, high DTI, negative net worth. Labels: 90+ Excellent,
80–89 Strong, 70–79 Stable, 60–69 Needs Attention, <60 At Risk.
**Weighting partially reworked — two concrete defects fixed:**
1. *Zero income silently passed the DTI check.* DTI is debt payments ÷ income, which
   `metrics.py::_safe_divide` stores as `0.0` when income is 0 — that fell through every threshold
   and read as a perfect 0% debt burden, so an unemployed user with real debt obligations was
   silently **credited** for it. Now flagged as "can't be assessed without recorded income" instead.
   Deliberately flagged, not penalized: the −25 for no income already reflects the root cause, so
   charging again would double-count one problem; the value added is transparency.
2. *Negative net worth was a flat −15 cliff* — −$1 and −$500,000 cost exactly the same. Now scaled
   against annual income (the standard "how deep is this hole relative to what you earn" reference):
   >2 years of income → −20/high, >6 months → −12/medium, else → −5/low. Falls back to the original
   flat −15 when income is 0, since there's no denominator to scale against. Thresholds are
   heuristics in the same spirit as the DTI/emergency-fund bands, not lender-grade rules.
*Still open (deliberately not attempted here — it's a redesign, not a reweight):* the score
saturates easily. It's purely subtractive, so 20% savings / 6mo EF / 20% DTI scores the same
perfect 100 as 50% savings / 12mo EF / 0% DTI — there's no differentiation above "solid." Adding
positive signals would mean restructuring the model, which Rule 1 puts out of scope for a
weighting pass. `tests/test_health.py` now covers this module (it previously had **no tests at
all**), including regression tests for both fixes above.

### Opportunity Engine (legacy/transitional)
Deterministic engine predating the Decision Engine; still powers the current briefing. Should
eventually be retired or absorbed — don't maintain two competing recommendation engines long-term.

### Database Backup & Restore
`db/backup.py` — `create_backup(label=None)`, `list_backups()`, `restore_backup(path)`,
`prune_backups(keep)`. `db/run_backup.py` is the CLI behind `make backup` / `list-backups` /
`restore` / `prune-backups`. Key decisions:
- **Uses sqlite3's native `Connection.backup()`, not a file copy.** Copying a live SQLite file
  can capture a torn state if a write is in flight or a WAL/journal exists; the native API takes
  a consistent snapshot even while the source is open, which matters because backups are taken
  from inside the running app.
- **Every backup is integrity-checked before being returned** (`PRAGMA integrity_check`) and
  discarded if it fails — a corrupt backup is worse than none, because it looks like protection.
- **Restore is destructive, so it first backs up the database it's about to overwrite**
  (labelled `pre-restore`). Restoring the wrong file is recoverable. Restore also refuses to run
  against a file that isn't a readable SQLite DB with an `accounts` table, failing *before*
  touching anything rather than halfway through.
- **`ensure_schema_up_to_date()` auto-backs-up (labelled `pre-migration`) only when migrations
  are actually pending** against a database that already holds data. It runs on every startup,
  so an unconditional backup would mean a file per launch. A failed backup logs and continues
  rather than blocking the upgrade — the app still needs a current schema to run at all.
- **`prune_backups()` is never called automatically.** Backups are the user's safety net and
  deleting them is irreversible, so it stays explicit (`make prune-backups keep=N`). Growth is
  slow in practice since automatic backups only happen before a migration or a restore.
- **Not yet wired into the desktop UI** — backend + CLI only. The Settings page is still a
  placeholder; surfacing backup/restore there is the natural follow-up.

### Timeline Engine
`save_snapshot(month)`, `get_latest_snapshot()`, `get_previous_snapshot()`,
`compare_snapshots(previous, current)`. Each metric change is classified improved/worsened/neutral
with significance high (≥10%), medium (≥3%), low (<3%). "Better when increasing": assets, net
worth, cash, income, cash flow, savings rate, emergency fund months. "Better when decreasing":
debt, expenses, DTI. These are heuristics, not universal truths.

### Decision Engine
`FinancialDecision(title, description, priority, expected_impact_score, confidence_score,
ease_multiplier, time_horizon, reasoning, reversible)`, ranked into a `DecisionSet`.
Score = expected_impact × (confidence / 100) × ease_multiplier.
Rules: emergency fund < 3mo → build it; DTI > `DTI_ELEVATED` → reduce debt; negative cash flow →
stabilize; positive cash flow + 6mo+ EF + DTI ≤ `DTI_CONSERVATIVE` → optimize capital allocation;
else → maintain plan. (Bands come from `finance/thresholds.py` — see §5.)
**Both pieces of known debt here are resolved:**
- *Renamed `difficulty_score` → `ease_multiplier`.* The old name read backwards: the value is a
  multiplier where **higher ranks a decision higher**, so it was always measuring ease, not
  difficulty. Engine values are unchanged (0.5–1.0), so scores are byte-identical — verified
  against the demo database.
- *Circular import removed.* `decision_score()` now takes three plain numbers
  (`expected_impact_score`, `confidence_score`, `ease_multiplier`) instead of a `FinancialDecision`,
  so `scoring.py` imports nothing from `models.py` and the dependency runs one way only
  (models → scoring). `FinancialDecision.score` therefore imports `decision_score` at module level
  like anything else, instead of doing a function-local import to dodge the cycle. The `.score`
  property itself was **kept deliberately** — it's a genuinely derived value with four call sites
  (`decision/engine.py`'s sort, both formatters, `report_cards.py`), and deleting it would just
  push the same computation into each caller. The debt was the cycle workaround, not the property.
  `tests/test_decision_scoring.py` includes a regression guard that fails if the cycle returns.

### Executive Report Engine
`ExecutiveReport(month, snapshot, important_changes, strengths, concerns, recommended_focus,
top_decisions)`. `create_executive_report(month, persist=True)`: with `persist=True` (default)
saves a snapshot and compares to the previous one; with `persist=False` computes the snapshot
fresh and compares to the latest saved one without writing anything. Keeps medium/high changes,
derives strengths/concerns, ranks decisions via `generate_decisions_from_db()`.
**Partially resolved known issue:** `persist=False` (used by the desktop UI's summary cards, which
render on every page visit) no longer duplicates history on repeated reads. `persist=True`
(the "Generate Briefing" path) still saves a new snapshot per click, by design — see §8.

### AI Architecture
Principle: *Python calculates. Python structures. AI reasons. AI communicates.*
`AIRuntime.ask(prompt, context, temperature)` loads a markdown prompt asset, builds messages,
calls the LM Studio client, returns text — **no business logic here**.
`StrategicAdvisor.executive_briefing(month)` and `explain_scenario(month, scenario)` are the
finance-specific facades; both consume the new `ExecutiveReport`/`ScenarioResult` formatters, not
the old `briefing_summary()` string. `StrategicAdvisor.chat(month, messages)` is the multi-turn
facade behind the AI Advisor chat page — it folds the same read-only (`persist=False`) executive
report into a system message alongside the `strategic_advisor.md` prompt, then delegates to
`AIRuntime.chat()`, a multi-turn sibling of `ask()` that threads a growing user/assistant message
history rather than a single one-shot exchange. Prompt assets live in `assets/prompts/`;
`executive_briefing.md`, `scenario.md`, and `strategic_advisor.md` are implemented, the rest
(`financial_qa.md`, `goal_planning.md`, `explain_decision.md`) are still placeholders. Thinking-state models
(`ThinkingPhase`: build context → review changes → analyze decisions → generate response, corrected
from an earlier version that described a health/confidence-score review step the current pipeline
never performs) are wired into a background-threaded UI request via `ai/background.py`'s
`BackgroundTask` and `ai/thinking.py`'s `ThinkingAnimator` — see `BriefingView`/`BriefingPresenter`.

---

## 6. Development Environment

- **Hardware/OS:** MacBook Pro, Apple Silicon M5 Max, 48GB unified memory, macOS Tahoe 26.5.1
- **Python:** official python.org **3.12.10** (not 3.14; Homebrew Python breaks the GUI — lacks `_tkinter`)
- **Env/package manager:** `uv`
- **UI toolkit:** CustomTkinter (PySide6 was tried and abandoned — repeated native `cocoa` plugin crashes)
- **Local AI:** LM Studio, OpenAI-compatible endpoint at `http://localhost:1234/v1` — no API key, no cloud account
- **Likely deps:** SQLAlchemy, Pydantic, python-dotenv, pandas, openpyxl, openai (as a localhost client only), customtkinter, pytest, ruff

### Commands
```bash
cd "/Users/lonezebra/Documents/Projects/AI-Projects/finance-ai"
source .venv/bin/activate

make test          # PYTHONPATH=src pytest
make init-db       # create the DB fresh, or migrate an existing one -- both via Alembic now
make reset-db      # delete the DB file, recreate it via migrations
make db-migrate    # message="..." -- generate a new migration from model changes
make db-upgrade    # apply pending migrations without deleting existing data (same call as init-db)
make backup        # back up the database now (optional label="...")
make list-backups  # show available backups, newest first
make restore       # file=backups/finance-....db -- restore, saving current state first
make prune-backups # keep=10 -- delete all but the newest N backups
make import-demo   # import demo workbook
make briefing      # print deterministic briefing
make run           # launch desktop app
uv sync --dev      # install/sync deps

# Strategic Advisor smoke test (LM Studio must be running with a model loaded):
PYTHONPATH=src python -c "from finance_ai.ai.advisor import StrategicAdvisor; print(StrategicAdvisor().executive_briefing())"

git status && git add . && git commit -m "..." && git push
```

### Local model evaluation (M5 Max, 48GB)
| Model | Response time | Recommended role |
|---|---|---|
| Gemma4 26B A4B | ~15s | Daily executive briefings (clearer, faster, good capital-allocation framing) |
| Qwen 3.6 27B Dense | ~65s | Deep strategic analysis / scenario discussion (too slow for routine UI) |

A 9B-class model is worth considering as a fast fallback. Benchmarking is developer-only/offline —
don't auto-invoke multiple models in normal app flow.

### Known test suite (~7 tests at handoff time)
- Opportunities: low confidence prioritizes data quality; opportunities sort by score
- Timeline: changed metrics detected; debt decrease → improved; large cash increase → high significance
- Decision: low emergency fund → build emergency fund; stable snapshot → optimize capital allocation

---

## 7. Working With This User

The user knows how to code but is returning to it after several years away. When implementing:

- Explain *why* a file or pattern exists, not just what it does.
- Proceed step by step; don't dump unrelated code.
- Give the exact file path and state the file's purpose before code.
- For **new files**, give complete contents. For **large/core existing files**, ask for the current
  contents first, or provide a targeted diff — don't blind-rewrite.
- Include a test command and the expected result with every change.
- Keep product/philosophical reflection to end-of-sprint retrospectives, not every commit.
- Don't propose architecture pivots unless there's a genuine blocker.
- Every sprint should end with: code runs, tests pass, docs updated where relevant, no personal
  financial data committed, changes committed to git.

---

## 8. Known Issues & Technical Debt

### Cross-Cutting Concerns Checklist (standing requirement — see Rule 8)

Raised by the user after the desktop UI work began; not a one-time task, a lens to apply to
every feature going forward. Weigh these when scoping new work; fold real fixes in incrementally
rather than deferring to one giant hardening pass.

- **Error handling:** every user-facing entry point (desktop UI, CLI commands) should fail with a
  message a non-technical user could act on, not a raw traceback. Current gap: only a handful of
  files anywhere in `src/` have any `try`/`except` at all (`ai/background.py`'s catch-and-forward
  pattern and `ai/errors.py`'s friendly LM Studio message are the model to follow); DB-missing or
  DB-empty states aren't handled anywhere.
- **Security:** calibrated to this app's actual threat model — local-first, single-user, no
  network exposure beyond the localhost LM Studio call, no auth needed. All DB access already goes
  through the SQLAlchemy ORM (no raw SQL found, no injection surface). Known gap: the SQLite file
  is unencrypted at rest — today that relies on OS-level disk encryption (e.g. FileVault), not
  app-level; revisit only if the user explicitly wants app-level encryption.
- **Observability:** `logs/` (`LOG_DIR` in `config.py`) and the `audit_log` table both exist.
  **Started** — `logging_config.py::configure_logging()` wires the `finance_ai` logger (parent of
  every `finance_ai.*` module logger) to a rotating file at `LOG_DIR/finance_ai.log`; called once
  from `bootstrap_app()` (desktop app) and from `run_import.py`'s CLI entrypoint. `imports/importer.py`
  logs import start/completion/failure — the first (and so far only) module actually using it.
  Everything else in `src/` is still unlogged; add calls to the existing logger as each area is
  touched, rather than in one sweep. Wire `audit_log` in once an actual AI-driven data-mutation
  feature exists (ties to Rule 4) — building it against nothing yet would be speculative; nothing
  shipped so far mutates data on the AI's behalf.
- **Scalability:** not a multi-tenant concern here — the real question is whether SQLite/pandas
  hold up as one user's transaction history grows over years. They do, comfortably, so this stays
  low-risk as long as nothing breaks the local-first, single-process assumption.

**High priority (before public beta):**
1. **Done.** `import_dataset()` (`imports/importer.py`) upserts accounts, categories, debts,
   assets, budgets, and goals by natural key (name; month+category for budgets), and skips
   transactions that exactly match one already in the database (full-row fingerprint: date,
   merchant, description, amount, account, category, notes). Returns a typed `ImportResult`
   (created/updated/skipped_duplicate per entity) instead of a flat counts dict — `run_import.py`,
   `ImportPresenter.confirm_import()`, and `ImportView` all updated to match. Within-batch
   duplicates (the same row appearing twice in one workbook) are also caught, not just
   across-import duplicates. Known, accepted limitation: the transaction fingerprint requires an
   *exact* match on every field — editing so much as a note on a re-imported transaction makes it
   look new rather than updating the original. Real bank-transaction dedup (stable external IDs)
   is out of scope until there's an actual bank API integration to provide them.
2. **Done.** Alembic manages schema changes now (`alembic.ini` + `alembic/` at repo root,
   `db/migrate.py::ensure_schema_up_to_date()`). Model changes ship as a generated migration
   (`make db-migrate message="..."`) instead of requiring `make reset-db` to wipe the database.
   `ensure_schema_up_to_date()` runs on every app/CLI startup (`bootstrap_app()`,
   `db/init_db.py`) and handles three cases: a fresh install (no DB yet) gets every table
   created via the baseline migration onward; a database that predates migrations entirely
   (has the app's tables but no `alembic_version` table) is *stamped* at the baseline
   revision rather than having that migration's `CREATE TABLE` statements run against
   tables that already exist — safe because the baseline migration was autogenerated from
   exactly this schema — so existing user data is never touched, only marked as already
   current; a database already migration-tracked just gets any pending migrations applied
   normally. `make init-db`/`make reset-db` both route through this automatically (no
   Makefile changes needed there); `make db-upgrade` is a differently-named alias for the
   same call, for the "I have data, bring the schema up to date" mental model.
3. **Partially done.** `create_executive_report()` now takes a `persist` parameter — `persist=False`
   (used by the briefing's summary cards, which render on every page visit) computes the snapshot
   fresh and compares against `get_latest_snapshot()` without writing anything, so viewing no longer
   duplicates history. `persist=True` (the default, used by "Generate Briefing") still saves a new
   snapshot per click — that part of the original issue is unchanged, deliberately, since clicking
   Generate is treated as an explicit check-in worth recording.
4. **Done** — see `reports/formatter.py` and `format_executive_report_for_ai()`.
5. **Done** — `StrategicAdvisor.executive_briefing()` now calls `create_executive_report()` →
   `format_executive_report_for_ai()` → `AIRuntime.ask()`.
6. **Done** — `ai/background.py`'s `BackgroundTask` + `ai/thinking.py`'s `ThinkingAnimator`, wired
   into `BriefingView`/`BriefingPresenter`.
7. **Done** — see `ai/errors.py::describe_ai_error()`.
8. **Largely done — audited before the private→public flip.** Full-history audit
   (`git log --all --diff-filter=A`) found exactly one database file ever committed:
   `data/finance 2.db`, a macOS duplicate-save artifact that slipped past the old
   exact-filename `data/finance.db` ignore rule (the space in the name meant it didn't
   match). **Verified empty — 0 rows across all 10 tables in the committed blob, not just
   the working copy — so no financial data was ever exposed.** It has been removed from the
   tree, along with stray `src/UNKNOWN.egg-info/` build artifacts. `.gitignore` is now
   pattern-based (`*.db`, `*.sqlite`, `*.egg-info/`, …) rather than naming one exact file,
   so a renamed or duplicated database can't slip through the same way again. Also audited
   clean: no `.env` files, no `.xlsx`/`.csv` data files (only the committed
   `finance_template.xlsx`), and no credentials — the sole `API_KEY` in the codebase is
   `LM_STUDIO_API_KEY = "lm-studio"`, the placeholder LM Studio requires and ignores, not a
   real secret. **Deliberately not history-rewritten:** purging the old commit would break
   every existing clone/fork and rewrite all downstream hashes, which is disproportionate
   for a provably empty file. *Remaining nit (cosmetic, not a leak):* `CLAUDE.md` §6 and
   `docs/COMMANDS.md` hardcode `/Users/lonezebra/...` dev paths — the username matches the
   public GitHub handle so nothing new is revealed, but they read as noise to anyone who
   clones the repo.

**Medium priority:** consolidate Opportunity + Decision engines; rename `difficulty_score` to
something like an ease/feasibility multiplier; move decision scoring out of the model property;
**data-freshness signal for Confidence Score — done, see §5**; **Health Score weighting — two
concrete defects fixed, see §5; the "score saturates easily" limitation remains open**;
essential-expense-only emergency fund calc; **asset/account double counting — detection done,
see §5**; **DTI basis
(gross vs net) — done, see §5**; audit-log integration (import batch integration is done — see
§10.D); **database backup & restore — done, see §5**.

**Lower priority / later release:** Ollama provider adapter; cross-platform packaging; Windows
verification; bank API integration; investment analytics; retirement readiness; tax/insurance modules.

---

## 9. Immediate Next Task

**Status: complete.** The formatter, advisor wiring, and Scenario Engine described below have all
shipped. See §10 for what's actually next.

<details>
<summary>Original task text (kept for history)</summary>

**Build `src/finance_ai/reports/formatter.py`:**
- Take an `ExecutiveReport`.
- Produce concise, structured, AI-readable context: snapshot facts, important changes, strengths,
  concerns, recommended focus, top decisions with deterministic reasoning.

**Then update `src/finance_ai/ai/advisor.py`** so `StrategicAdvisor.executive_briefing()` calls, in order:
1. `create_executive_report(month)`
2. `format_executive_report_for_ai(report)`
3. `AIRuntime.ask(prompt="executive_briefing", context=formatted_report)`

Add formatter tests that don't require LM Studio to be running.

**Do not begin Scenario Engine work until this integration is complete and tested.**

</details>

---

## 10. Near-Term Roadmap (in order)

**A. Executive Report → AI integration** — **Done.** (formatter, advisor update, tests — see §9)

**B. Scenario Engine** — **Done.** Inputs: income change, recurring expense change, extra debt
payment, savings/investment contribution change, one-time purchase, one-time windfall. Outputs:
projected snapshot, comparison vs. current, projected decisions, deterministic scenario facts, AI
explanation. v1 scope notes in `ROADMAP.md` under "Version 0.6" (single-month projection only, no
persistence, no DTI recalculation on debt payment). Desktop UI for this shipped as D5 — see §10.D.

**C. Decision Engine 2.0** — **Done.** Debt-specific payoff candidates (avalanche-ranked),
emergency-fund target candidate with real dollar gap, investment candidate, goal-funding candidate.
Deferred to a follow-up (see `ROADMAP.md` "Version 0.7"): wiring decision candidates to
auto-generated Scenario projections ("compare decisions through scenarios").

**D. Desktop product workflow** — **In progress.**
- D1 (real AI briefing + background threading + thinking state): **Done.**
- D2 (Executive Briefing summary cards): **Done.**
- D3 (import workflow: choose/preview/confirm): **Done.** Also wired up the previously-dormant
  `import_batches` table (records a row per successful import) and added
  `imports/errors.py::describe_import_error()` for friendly duplicate-key messages. Import
  idempotency (known issue #1, originally deferred here) has since been fixed — see §8.
- D4 (Strategic Advisor chat): **Done.** Wired the existing "AI Advisor" sidebar placeholder into
  a real multi-turn chat: `ChatPresenter` (same `attach()`/`detach()` + defensive
  `tkinter.TclError` pattern as `BriefingPresenter`, owned by `MainWindow` so a conversation
  survives navigating away and back) plus `ChatView` (scrollable bubble transcript, text input,
  indeterminate progress bar while a reply is in flight, auto-scroll to the newest message).
  In-memory only — conversations are lost on app restart, no new persistence/schema change this
  pass (see Known Issues: chat history persistence is not tracked as a gap, just an intentional v1
  scope cut). Deliberately does not reuse the executive briefing's 4-phase `ThinkingAnimator` — those
  phases describe report generation specifically and would mislabel a plain chat turn.
- D5 (Scenario Planning UI): **Done.** New "Scenario Planning" sidebar page — the first page added
  outright rather than filling an existing placeholder slot. `ScenarioPresenter` follows the same
  `attach()`/`detach()` + defensive `tkinter.TclError` pattern as `BriefingPresenter`/`ChatPresenter`,
  owned by `MainWindow`, but uses a single `on_change()` callback rather than per-event callbacks —
  its state is a builder (an editable list of adjustments) plus a result plus an AI narrative, closer
  to "re-render from current state" than the mostly-append-only state the other two presenters track.
  `ScenarioView` splits into a builder (add/remove `ScenarioAdjustment` rows via a type dropdown,
  amount, and label, each type captioned with its sign convention since income/expense changes are
  signed but debt-payment/contribution/purchase/windfall amounts are entered as positive magnitudes)
  and a results area. "Run Scenario" calls `run_scenario()` synchronously (fast, deterministic, no
  AI) and renders projected-vs-baseline cards by reusing `report_cards.py`'s existing card builders
  (`build_changes_card` fed via `interpret_comparison(result.comparison)`, `build_snapshot_card`,
  `build_decisions_card`) plus two new ones added there (`build_scenario_facts_card`,
  `build_ai_narrative_card`). "Explain with AI" is a separate, explicit action (background-threaded,
  same `BackgroundTask` as chat/briefing) that calls `StrategicAdvisor.explain_scenario()` — kept
  separate from "Run Scenario" itself so the fast deterministic path never blocks on LM Studio.
  Uses the same lightweight "thinking..." status + indeterminate progress bar as chat, not the
  briefing's 4-phase animator, for the same reason as D4. Supports multiple adjustments per scenario
  (the engine already models `Scenario.adjustments` as a list) rather than a single-adjustment v1 —
  manually verified a compound raise + extra-debt-payment scenario composes correctly against the
  real demo database.

**E. Public beta criteria** — keep the repo private until a user can: clone/install with clear
instructions, launch reliably, import a workbook, see an Executive Briefing, run a scenario, ask
the Strategic Advisor about it, and understand caveats/data confidence.

---

## 11. Demo Data (reference only — do not use to judge real-world score quality)

Total assets $647,500 · Total debt $29,500 · Net worth $618,000 · Cash $12,500 · Monthly income
$3,500 · Monthly expenses $225.50 · Monthly cash flow $3,274.50 · Savings rate 93.6% · DTI 19.0% ·
Emergency fund 55.4 months. Mathematically correct but financially unrealistic (omits most
household expenses) — it validates the pipeline, not the scoring quality.

---

## 12. Further Reading

- `OPEN_CFO_PROJECT_HANDOFF.md` — the full handoff this file is distilled from (all detail, edge
  cases, and rationale live there)
- `CURRENT_STATE.json` — machine-readable snapshot of implemented features and open issues
- `NEW_MODEL_BOOTSTRAP_PROMPT.md` — the original bootstrap prompt for a new AI model on this project
- `reconstructed_project/` — best-effort recovered source tree (context aid, not guaranteed exact)
- `reconstructed_project/docs/` — `ARCHITECTURE_CURRENT.md`, `NEXT_SPRINT.md`,
  `DEVELOPMENT_SETUP_CURRENT.md`, plus uploaded reference versions of `PRODUCT_SPEC`, `ENGINEERING`,
  `COMMANDS`, `README`, `ROADMAP`
