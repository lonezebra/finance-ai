# Open CFO Development Commands

This document contains the most commonly used commands while developing Open CFO.

---

# Opening the Project

```bash
cd "/Users/lonezebra/Documents/Projects/AI-Projects/finance-ai"
```

---

# Activate the Python Environment

```bash
source .venv/bin/activate
```

Verify:

```bash
python --version
which python
```

Expected:

- Python 3.12.x
- `.venv/bin/python`

---

# Make Commands

## Show available commands

```bash
make help
```

## Run tests

```bash
make test
```

## Initialize database

```bash
make init-db
```

## Reset database

```bash
make reset-db
```

## Import demo workbook

```bash
make import-demo
```

## Show Executive Briefing

```bash
make briefing
```

## Git status

```bash
make status
```

## Push commits

```bash
make push
```

---

# Manual Commands

## Run tests

```bash
PYTHONPATH=src pytest
```

## Initialize the database

```bash
PYTHONPATH=src python -m finance_ai.db.init_db
```

## Import the demo workbook

```bash
PYTHONPATH=src python -m finance_ai.imports.run_import
```

## Display the Executive Briefing

```bash
PYTHONPATH=src python -c "from finance_ai.finance.briefing_summary import briefing_summary; print(briefing_summary('2026-06'))"
```

---

# Git Workflow

## Check status

```bash
git status
```

## Commit work

```bash
git add .
git commit -m "Describe the completed sprint"
```

## Push to GitHub

```bash
git push
```

---

# Sprint Workflow

Every sprint follows the same pattern.

1. Design
2. Implement
3. Test
4. Commit
5. Update documentation

Never skip testing before committing.

---

# Project Structure

```
finance-ai/

docs/
src/
tests/
data/
backups/
logs/
reports/

pyproject.toml
README.md
Makefile
```

---

# Current Architecture

```
Excel
   ↓
Import Engine
   ↓
SQLite
   ↓
Finance Engine
   ↓
Decision Engine
   ↓
Open CFO Engine
   ↓
Executive Briefing
   ↓
AI Advisor
```