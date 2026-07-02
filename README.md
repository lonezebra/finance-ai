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
- Local AI reasoning
- Scenario planning
- Structured financial workflows

Everything runs locally.

Your financial data remains on your computer.

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

Open CFO uses **Qwen 3.6** running locally through **LM Studio**.

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
 AI Advisor (Qwen)
```

---

# Current Features

- SQLite financial database
- Structured Excel templates
- Financial Snapshot
- Financial Health Score
- Financial Confidence Score
- Executive Briefing
- Decision Engine
- Automated unit tests

---

# Planned Features

## Version 0.2

- Excel validation
- Workbook import
- Import reports
- Audit logging

## Version 0.3

- Desktop Dashboard (PySide6)

## Version 0.4

- Local AI Advisor
- LM Studio integration
- Conversation history

## Version 0.5

- Scenario Planning Engine
- What-if analysis

## Version 0.6

- Interactive dashboard
- Charts
- Financial timeline

## Version 1.0

Open CFO release.

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