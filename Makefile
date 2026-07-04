.PHONY: help activate test reset-db init-db import-demo briefing run status push

help:
	@echo "Open CFO development commands"
	@echo ""
	@echo "make test        Run tests"
	@echo "make init-db     Initialize database"
	@echo "make reset-db    Delete and recreate database"
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