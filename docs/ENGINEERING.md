# Engineering Principles

Open CFO is a local-first personal CFO application.

This document defines how the project should be built and maintained.

## Core Principles

### 1. Protect the user's financial data

Financial data is sensitive.

The system should default to:
- local storage
- explicit user confirmation
- backups before destructive actions
- clear audit history

### 2. Python calculates/structures, AI reasons/communicates

Deterministic calculations belong in Python.

Examples:
- net worth
- cash flow
- savings rate
- debt-to-income ratio
- emergency fund coverage
- financial health score
- financial confidence score
- decision ranking

The AI Advisor should explain, interpret, compare, and help plan.

### 3. SQLite is the source of truth

Excel is for humans.

SQLite is for the application.

All dashboards, reports, decisions, and AI summaries should eventually read from SQLite.

### 4. Excel is the human data interface

Users should be able to maintain structured financial data through Excel templates.

The import pipeline should validate data before storing it.

### 5. Every recommendation must be explainable

Open CFO should not produce black-box advice.

Every recommendation should include:
- what changed
- why it matters
- supporting calculations
- confidence level
- tradeoffs

### 6. Every score must be reproducible

Financial Health, Financial Confidence, and Decision Scores must be based on deterministic rules.

The same input should produce the same output.

### 7. Small commits

Each commit should represent one coherent improvement.

Avoid giant commits that mix unrelated changes.

### 8. Working software at every checkpoint

Every sprint should end with:
- code that runs
- tests passing
- changes committed
- documentation updated when needed

### 9. Prefer clarity over cleverness

This project should be easy to understand months later.

Readable code is more valuable than clever code.

### 10. No silent data changes

Any future data-changing AI action must:
- propose the action
- show the user what will change
- require confirmation
- write to the audit log
- create a backup when appropriate

### 11. AI should never replace deterministic logic

AI should enhance user understanding.

Business rules and financial calculations remain deterministic and testable.

## Development Workflow

Each sprint follows:

1. Design
2. Implement
3. Test
4. Commit
5. Document

## Quality Gates

Before a sprint is complete:

- Code runs
- Tests pass
- No personal financial data is committed
- Public interfaces are understandable
- Important decisions are documented