.PHONY: help activate test reset-db init-db db-migrate db-upgrade import-demo briefing run status push

help:
	@echo "Open CFO development commands"
	@echo ""
	@echo "make test        Run tests"
	@echo "make init-db     Initialize database (creates it fresh, or migrates an existing one)"
	@echo "make reset-db    Delete the database file and recreate it via migrations"
	@echo "make db-migrate  Generate a new migration from model changes (message=\"...\")"
	@echo "make db-upgrade  Apply any pending migrations without deleting existing data"
	@echo "make import-demo Import demo Excel workbook"
	@echo "make briefing    Print Open CFO briefing"
	@echo "make status      Show git status"
	@echo "make push        Push commits"
	@echo "make run         Run Open CFO app"

test:
	PYTHONPATH=src pytest

init-db:
	PYTHONPATH=src python -m finance_ai.db.init_db

reset-db:
	rm -f data/finance.db
	PYTHONPATH=src python -m finance_ai.db.init_db

db-migrate:
	PYTHONPATH=src alembic revision --autogenerate -m "$(message)"

db-upgrade:
	PYTHONPATH=src python -m finance_ai.db.init_db

import-demo:
	PYTHONPATH=src python -m finance_ai.imports.run_import

briefing:
	PYTHONPATH=src python -c "from finance_ai.finance.briefing_summary import briefing_summary; print(briefing_summary('2026-06'))"

status:
	git status

push:
	git push

run:
	PYTHONPATH=src .venv/bin/python -m finance_ai.ui.app