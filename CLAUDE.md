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
├── backups/, logs/, reports/
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
**Known limitation:** imports are not idempotent yet (see Known Issues).

---

## 5. Core Domain Objects & Rules

### FinancialSnapshot
`month, total_assets, total_debt, net_worth, cash_balance, monthly_income, monthly_expenses,
monthly_cash_flow, savings_rate, debt_to_income_ratio, emergency_fund_months`

Calculations:
- `total_assets` = sum(account balances) + sum(asset values) — *risk of double-counting overlap*
- `net_worth` = total_assets − total_debt
- `monthly_income` = sum of positive transactions in month
- `monthly_expenses` = abs(sum of negative transactions in month)
- `monthly_cash_flow` = income − expenses
- `savings_rate` = cash_flow / income (0 if income is 0)
- `debt_to_income_ratio` = sum(debt minimum payments) / monthly income (simplified, not lender-grade)
- `emergency_fund_months` = cash_balance / monthly_expenses (uses *all* expenses, not essential-only)

### Financial Confidence Score
Measures data completeness/trustworthiness, **not** wealth. Starts at 100, subtracts for missing
accounts/transactions/categories/budgets/debts/assets/goals and for uncategorized transactions or
debts missing interest rates. Labels: 90+ High, 70–89 Moderate, 50–69 Low, <50 Very Low.
*Known weakness:* demo data scores 100/100 despite being sparse — needs freshness/coverage signals.

### Financial Health Score
Measures the financial condition itself. Starts at 100, subtracts for no income, negative cash
flow, low savings rate, low emergency fund, high DTI, negative net worth. Labels: 90+ Excellent,
80–89 Strong, 70–79 Stable, 60–69 Needs Attention, <60 At Risk.

### Opportunity Engine (legacy/transitional)
Deterministic engine predating the Decision Engine; still powers the current briefing. Should
eventually be retired or absorbed — don't maintain two competing recommendation engines long-term.

### Timeline Engine
`save_snapshot(month)`, `get_latest_snapshot()`, `get_previous_snapshot()`,
`compare_snapshots(previous, current)`. Each metric change is classified improved/worsened/neutral
with significance high (≥10%), medium (≥3%), low (<3%). "Better when increasing": assets, net
worth, cash, income, cash flow, savings rate, emergency fund months. "Better when decreasing":
debt, expenses, DTI. These are heuristics, not universal truths.

### Decision Engine
`FinancialDecision(title, description, priority, expected_impact_score, confidence_score,
difficulty_score, time_horizon, reasoning, reversible)`, ranked into a `DecisionSet`.
Score = expected_impact × confidence × difficulty("ease") multiplier.
Rules: emergency fund < 3mo → build it; DTI > 36% → reduce debt; negative cash flow → stabilize;
positive cash flow + 6mo+ EF + DTI ≤25% → optimize capital allocation; else → maintain plan.
*Known debt:* `FinancialDecision.score` imports scoring inside a property to dodge a circular
import — fine for now, don't stop feature work to fix it.

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
make init-db       # PYTHONPATH=src python -m finance_ai.db.init_db
make reset-db      # delete + recreate database
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
- **Observability:** `logs/` (`LOG_DIR` in `config.py`) and the `audit_log` table both exist but
  nothing writes to either — zero uses of Python's `logging` module anywhere in `src/`. Add basic
  logging (imports, snapshot creation, AI calls, errors) as features are built, not after the fact.
  Wire `audit_log` in once an actual AI-driven data-mutation feature exists (ties to Rule 4) —
  building it against nothing yet would be speculative; nothing shipped so far mutates data on the
  AI's behalf.
- **Scalability:** not a multi-tenant concern here — the real question is whether SQLite/pandas
  hold up as one user's transaction history grows over years. They do, comfortably, so this stays
  low-risk as long as nothing breaks the local-first, single-process assumption.

**High priority (before public beta):**
1. Import idempotency / duplicate handling
2. Real database migrations instead of reset-on-schema-change
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
8. Guarantee no personal financial data is ever committed to git

**Medium priority:** consolidate Opportunity + Decision engines; rename `difficulty_score` to
something like an ease/feasibility multiplier; move decision scoring out of the model property;
add data-freshness signal to Confidence Score; improve Health Score weighting; essential-expense-only
emergency fund calc; avoid asset/account double counting; better DTI methodology (gross vs net
income); audit-log integration (import batch integration is done — see §10.D); database backup &
restore.

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
persistence, no DTI recalculation on debt payment).

**C. Decision Engine 2.0** — **Done.** Debt-specific payoff candidates (avalanche-ranked),
emergency-fund target candidate with real dollar gap, investment candidate, goal-funding candidate.
Deferred to a follow-up (see `ROADMAP.md` "Version 0.7"): wiring decision candidates to
auto-generated Scenario projections ("compare decisions through scenarios").

**D. Desktop product workflow** — **In progress.**
- D1 (real AI briefing + background threading + thinking state): **Done.**
- D2 (Executive Briefing summary cards): **Done.**
- D3 (import workflow: choose/preview/confirm): **Done.** Also wired up the previously-dormant
  `import_batches` table (records a row per successful import) and added
  `imports/errors.py::describe_import_error()` for friendly duplicate-key messages. Deliberately
  did not add duplicate detection — import is still not idempotent (known issue #1); the UI just
  warns clearly and fails gracefully instead of crashing when a re-import collides.
- D4 (Strategic Advisor chat): **Done.** Wired the existing "AI Advisor" sidebar placeholder into
  a real multi-turn chat: `ChatPresenter` (same `attach()`/`detach()` + defensive
  `tkinter.TclError` pattern as `BriefingPresenter`, owned by `MainWindow` so a conversation
  survives navigating away and back) plus `ChatView` (scrollable bubble transcript, text input,
  indeterminate progress bar while a reply is in flight, auto-scroll to the newest message).
  In-memory only — conversations are lost on app restart, no new persistence/schema change this
  pass (see Known Issues: chat history persistence is not tracked as a gap, just an intentional v1
  scope cut). Deliberately does not reuse the executive briefing's 4-phase `ThinkingAnimator` — those
  phases describe report generation specifically and would mislabel a plain chat turn.

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
