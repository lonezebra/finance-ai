import re
import sqlite3

from sqlalchemy.exc import IntegrityError

# The only unique constraint in the schema today is Category.name, but this stays generic
# (table.column extracted from the DB error itself) rather than hardcoding that one case.
TABLE_SINGULAR = {
    "accounts": "account",
    "categories": "category",
    "transactions": "transaction",
    "debts": "debt",
    "assets": "asset",
    "budgets": "budget",
    "goals": "goal",
}


def describe_import_error(exc: Exception) -> str:
    duplicate = _describe_duplicate_key(exc)
    if duplicate:
        return duplicate

    return str(exc)


def _describe_duplicate_key(exc: Exception) -> str | None:
    if not isinstance(exc, IntegrityError) or not isinstance(exc.orig, sqlite3.IntegrityError):
        return None

    match = re.search(r"UNIQUE constraint failed: (\w+)\.(\w+)", str(exc.orig))
    if not match:
        return None

    table, column = match.groups()
    label = TABLE_SINGULAR.get(table, table)

    return (
        f"This looks like duplicate data -- a {label} with that {column} already exists in "
        "your database. Re-importing the same file isn't supported yet."
    )
