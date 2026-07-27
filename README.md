# Open CFO

> **Know what changed. Know what matters. Know what to do next.**

Open CFO is a **local-first, AI-powered Personal CFO** designed to help individuals and families make better financial decisions through deterministic financial calculations, transparent decision support, and private AI reasoning.

Unlike traditional budgeting software, Open CFO is not focused on simply tracking transactions.

Its purpose is to function like a personal Chief Financial Officer—analyzing your financial position, identifying opportunities, explaining tradeoffs, and helping you answer:

- What changed?
- What is risky?
- What should I do next?
- What happens if I choose a different path?

---

# Why Open CFO?

Most personal finance software tells you **what happened**.

Open CFO helps you decide **what to do next**.

The application combines:

- Deterministic financial calculations
- Transparent decision support
- Local AI Runtime
- Strategic Advisor powered by local LLMs
- Prompt Library
- Model-agnostic AI architecture
- Thinking state framework
- Scenario planning
- Structured financial workflows

Everything runs locally.

Your financial data remains on your computer.

---

# Getting Started

## Requirements

- Python 3.12+ (an official python.org build — on macOS, Homebrew Python lacks `_tkinter` and breaks the desktop UI)
- [uv](https://docs.astral.sh/uv/) for dependency management
- [LM Studio](https://lmstudio.ai/), running locally with a model loaded, for the AI-powered features (Executive Briefing narrative, AI Advisor chat, scenario explanations). Everything else works without it.

## Install

```bash
git clone <this-repo-url>
cd finance-ai
uv sync --dev
```

## Set up the database

```bash
make init-db
```

## Try it with demo data

```bash
make import-demo
make run
```

`make run` launches the desktop app. From there:

- **Import Data** — bring in your own Excel workbook (a starter template lives at `data/exports/finance_template.xlsx`)
- **Executive Briefing** — your financial snapshot plus an AI-generated narrative (requires LM Studio running)
- **Scenario Planning** — build a what-if (a raise, an extra debt payment, a windfall, ...) and see the projected impact, with an optional AI explanation (requires LM Studio running)
- **AI Advisor** — ask an ongoing chat about your finances (requires LM Studio running)

## Run the tests

```bash
make test
```

See `make help` for the full list of available commands.

---

# Philosophy

Open CFO is built around four core principles.

## Python Calculates

Financial calculations belong in deterministic code.

Examples:

- Net Worth
- Cash Flow
- Savings Rate
- Debt-to-Income Ratio
- Financial Health
- Financial Confidence
- Decision Ranking

---

## SQLite Stores

SQLite is the source of truth.

Everything inside Open CFO ultimately reads from SQLite.

---

## Excel Is for Humans

Users should not have to manually enter hundreds of transactions inside an application.

Open CFO provides structured Excel templates that can be:

- completed manually
- exported
- version controlled
- imported into Open CFO

---

## AI Explains

Open CFO talks to a local model through **LM Studio**. The AI Runtime is model-agnostic — any
model LM Studio can serve works; swap models without touching the rest of the application.

The AI does **not** perform financial calculations.

Instead, it:

- explains
- compares
- recommends
- summarizes
- answers questions
- performs scenario analysis

using data produced by the Finance Engine.

---

# Architecture

```text
Excel / CSV
      │
      ▼
 Import Engine
      │
      ▼
 SQLite Database
      │
      ▼
 Finance Engine
      │
      ▼
 Decision Engine
      │
      ▼
 Open CFO Engine
      │
      ▼
 Executive Briefing
      │
      ▼
 AI Advisor (local model via LM Studio)
```

---

# Current Features

- Local-first architecture
- SQLite financial database
- Structured Excel import pipeline, including idempotent re-import (upsert by natural key for
  accounts/categories/debts/assets/budgets/goals; exact-match duplicate detection for transactions)
- Workbook validation
- Financial Snapshot, Health, and Confidence engines (Confidence Score is surfaced in the
  Executive Briefing)
- Decision Engine (debt payoff, emergency fund, investment, and goal-funding candidates)
- Scenario Engine with a desktop UI (income/expense changes, extra debt payments, contribution
  changes, one-time purchases/windfalls; multiple adjustments per scenario), including an
  on-demand AI explanation of the projection
- Executive Briefing (deterministic snapshot cards plus an AI-generated narrative)
- Desktop app (CustomTkinter): Executive Briefing, Scenario Planning, Import Data, and AI Advisor
  chat are functional; Dashboard, Accounts, Transactions, Debt, Assets, Budget, Goals, Reports, and
  Settings are still placeholders
- Local AI Runtime and Strategic Advisor (LM Studio), including a multi-turn chat
- Prompt Library
- Thinking state framework
- Automated tests

---

# Planned Features

## Versions 0.2–0.6 — done

Excel import and validation with idempotent re-import, the desktop shell, the Strategic Advisor
(including the chat above), the Financial History Engine, and the Scenario Engine (backend and UI).

## Version 0.7 — in progress (public beta readiness)

- Dashboard and the remaining placeholder pages (Accounts, Transactions, Debt, Assets, Budget,
  Goals, Reports, Settings)

## Version 1.0

Open CFO public beta release

---

# Example Executive Briefing

```text
Good Morning, Alfred.

Financial Health

84 / 100

Financial Confidence

96 / 100

Today's Highest Impact Decision

Increase Roth IRA contribution by $200/month.

Expected Long-Term Impact

+$418,000

Confidence

96%

Tradeoff

Emergency fund reaches target one month later.
```

---

# Documentation

The `docs/` directory contains:

- Product Specification
- Architecture
- Domain Model
- Data Model
- Engineering Principles
- Roadmap
- Architecture Decision Records

---

# Engineering Philosophy

Open CFO follows a few simple rules.

- Python calculates.
- SQLite stores.
- Excel is for humans.
- AI explains.
- Every recommendation must be explainable.
- Every score must be reproducible.
- Small commits.
- Working software at every checkpoint.
- Protect user data.

---

# Long-Term Vision

Open CFO is not intended to become another budgeting application.

The long-term vision is to create a **local-first Personal CFO** capable of:

- Decision support
- Financial planning
- Scenario analysis
- Long-term wealth optimization
- Executive-style financial briefings

while keeping all user data private and under the user's control.

---

# License

TBD

---

> **Open CFO**
>
> *Know what changed. Know what matters. Know what to do next.*