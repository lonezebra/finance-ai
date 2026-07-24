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
│   ├── prompts/            # executive_briefing.md (implemented), strategic_advisor.md,
│   │                       # scenario.md, financial_qa.md, goal_planning.md,
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
│   ├── test_opportunities.py, test_timeline.py, test_decision_engine.py
└── src/finance_ai/
    ├── config.py
    ├── ai/          # runtime, advisor, thinking state, prompt loading
    ├── core/
    ├── db/          # SQLAlchemy models, init_db
    ├── decision/    # Decision Engine
    ├── exports/
    ├── finance/     # Finance Engine, Opportunity Engine (legacy)
    ├── history/     # Timeline Engine (snapshots, comparison, interpretation)
    ├── imports/     # reader, validator, mapper, importer
    ├── reports/     # Executive Report Engine (+ formatter.py — next task)
    └── ui/          # CustomTkinter desktop shell
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
top_decisions)`. `create_executive_report(month)` saves a snapshot, compares to previous, keeps
medium/high changes, derives strengths/concerns, ranks decisions.
**Known issue:** it saves a *new* snapshot on every call, including repeated reads — causing
duplicate history rows. Fix direction: snapshot on import/explicit refresh only, or read the
latest snapshot instead of always creating one.

### AI Architecture
Principle: *Python calculates. Python structures. AI reasons. AI communicates.*
`AIRuntime.ask(prompt, context, temperature)` loads a markdown prompt asset, builds messages,
calls the LM Studio client, returns text — **no business logic here**.
`StrategicAdvisor.executive_briefing(month)` is the finance-specific facade; currently still uses
the older `briefing_summary()` string instead of the new `ExecutiveReport` (this is the immediate
task, see §8). Prompt assets live in `assets/prompts/`; only `executive_briefing.md` is implemented,
the rest are placeholders. Thinking-state models exist (`ThinkingPhase`: build context → review
health → review confidence → analyze decisions → generate response) but aren't wired into a
background-threaded UI request yet.

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

**High priority (before public beta):**
1. Import idempotency / duplicate handling
2. Real database migrations instead of reset-on-schema-change
3. Snapshot lifecycle — stop creating duplicates on report reads
4. `ExecutiveReport` → AI-context formatter (see immediate task below)
5. `StrategicAdvisor` should consume `ExecutiveReport`, not the old briefing string
6. Background AI execution + loading/thinking state in the UI
7. Friendly "LM Studio offline" error handling
8. Guarantee no personal financial data is ever committed to git

**Medium priority:** consolidate Opportunity + Decision engines; rename `difficulty_score` to
something like an ease/feasibility multiplier; move decision scoring out of the model property;
add data-freshness signal to Confidence Score; improve Health Score weighting; essential-expense-only
emergency fund calc; avoid asset/account double counting; better DTI methodology (gross vs net
income); import batch/audit-log integration; database backup & restore.

**Lower priority / later release:** Ollama provider adapter; cross-platform packaging; Windows
verification; bank API integration; investment analytics; retirement readiness; tax/insurance modules.

---

## 9. Immediate Next Task

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

---

## 10. Near-Term Roadmap (in order)

**A. Executive Report → AI integration** (formatter, advisor update, tests — see §9)

**B. Scenario Engine** — inputs: income change, recurring expense change, extra debt payment,
savings/investment contribution change, one-time purchase, one-time windfall. Outputs: projected
snapshot, comparison vs. current, projected decisions, deterministic scenario facts, AI explanation.

**C. Decision Engine 2.0** — debt-specific payoff candidates, emergency-fund target candidate,
investment candidate, goal-funding candidate, expected-impact/tradeoff model, compare decisions
through scenarios.

**D. Desktop product workflow** — import workflow (choose/preview/confirm), Executive Briefing
cards, AI-generated narrative, thinking state, Strategic Advisor chat.

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
